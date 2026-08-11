def test_nlp_analysis(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    resp = client.post(
        "/api/v1/ai/nlp",
        json={"text": "Se afirma que el nuevo impuesto afectará a todos los ciudadanos."},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "mock"
    assert data["language"] == "es"
    assert "claims" in data
    assert "suspicious_signals" in data


def test_vision_analysis(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    resp = client.post(
        "/api/v1/ai/vision",
        files={"image": ("manipulada.png", b"\x89PNG\r\n\x1a\nfake-image-bytes", "image/png")},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "manipulation_score" in data
    assert "ocr_text" in data


def test_llm_explain(client, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    resp = client.post(
        "/api/v1/ai/explain",
        json={
            "payload": {"nlp": {"suspicious_signals": ["lenguaje_emocional"]}, "vision": []},
            "context": "Afirmación original",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommended_verdict"] in {"true", "false", "mixed", "unverified"}
    assert "summary" in data


def test_ai_health(client, regular_user, auth_headers):
    resp = client.get("/api/v1/ai/health", headers=auth_headers(regular_user))
    assert resp.status_code == 200
    assert resp.json()["provider"] == "mock"
