import time


def test_create_and_list_request(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    resp = client.post(
        "/api/v1/requests",
        data={"claim": "El gobierno anunció un nuevo bono de emergencia"},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["claim"].startswith("El gobierno")
    assert body["media_type"] == "text"
    assert body["status"] == "pending"

    listing = client.get("/api/v1/requests", headers=headers)
    assert listing.status_code == 200
    assert any(r["id"] == body["id"] for r in listing.json())


def test_create_request_with_image(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    resp = client.post(
        "/api/v1/requests",
        data={"claim": "Imagen de un accidente"},
        files={"images": ("foto.png", b"\x89PNG\r\n\x1a\nfake-image-bytes", "image/png")},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["media_type"] == "mixed"
    assert len(body["images"]) == 1


def test_user_cannot_access_other_users_request(client, regular_user, admin_user, auth_headers):
    owner = client.post(
        "/api/v1/requests",
        data={"claim": "Afirmación privada"},
        headers=auth_headers(regular_user),
    ).json()

    other = client.get(
        f"/api/v1/requests/{owner['id']}", headers=auth_headers(admin_user)
    )
    assert other.status_code == 200  # admin sí puede

    # creamos un usuario sin permisos
    client.post(
        "/api/v1/auth/register",
        json={"email": "ajeno@test.com", "full_name": "Ajeno", "password": "password123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ajeno@test.com", "password": "password123"},
    ).json()
    ajeno_headers = {"Authorization": f"Bearer {login['access_token']}"}

    resp = client.get(f"/api/v1/requests/{owner['id']}", headers=ajeno_headers)
    assert resp.status_code == 403


def test_process_request_pipeline(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    req = client.post(
        "/api/v1/requests", data={"claim": "Afirmación a verificar con IA"}, headers=headers
    ).json()

    resp = client.post(f"/api/v1/requests/{req['id']}/process", headers=headers)
    assert resp.status_code == 202

    detail = None
    for _ in range(50):
        detail = client.get(f"/api/v1/requests/{req['id']}", headers=headers).json()
        if detail["status"] in ("completed", "failed"):
            break
        time.sleep(0.2)

    assert detail["status"] == "completed"
    assert detail["verdict"] is not None
    assert len(detail["analyses"]) >= 2  # nlp + llm
    stages = {a["stage"] for a in detail["analyses"]}
    assert "nlp" in stages
    assert "llm" in stages


def test_verdict_only_for_verifier(client, regular_user, verifier_user, auth_headers):
    req = client.post(
        "/api/v1/requests", data={"claim": "Afirmación para dictamen"}, headers=auth_headers(regular_user)
    ).json()

    denied = client.post(
        f"/api/v1/requests/{req['id']}/verdict",
        json={"verdict": "true", "confidence": 0.9},
        headers=auth_headers(regular_user),
    )
    assert denied.status_code == 403

    ok = client.post(
        f"/api/v1/requests/{req['id']}/verdict",
        json={"verdict": "true", "confidence": 0.9},
        headers=auth_headers(verifier_user),
    )
    assert ok.status_code == 200
    assert ok.json()["verdict"] == "true"
    assert ok.json()["confidence"] == 0.9
