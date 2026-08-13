from app.services.detection_service import classify_image

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-image-content-for-tests"


def _upload(client, filename="foto.png", content=PNG_BYTES, data=None):
    return client.post(
        "/api/v1/detect/image",
        files={"file": (filename, content, "image/png")},
        data=data or {},
    )


def test_detect_image_returns_full_report(client):
    resp = _upload(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] in ("autentica", "sospechosa", "manipulada")
    assert body["verdict_label"]
    assert body["risk_score"] >= 0
    assert 0 <= body["manipulation_score"] <= 1
    assert 0 <= body["deepfake_score"] <= 1
    assert body["ocr_text"] is not None
    assert isinstance(body["objects"], list)
    assert body["explanation"]
    assert body["provider"] == "mock"
    assert body["checked_at"]
    assert body["metadata"]["file_size_bytes"] == len(PNG_BYTES)


def test_detect_image_accepts_claim_context(client):
    resp = _upload(client, data={"claim": "Supuesto video de un político"})
    assert resp.status_code == 200
    assert resp.json()["claim"] == "Supuesto video de un político"


def test_detect_image_rejects_invalid_extension(client):
    resp = _upload(client, filename="documento.txt", content=b"hola")
    assert resp.status_code == 415


def test_detect_image_requires_file(client):
    resp = client.post("/api/v1/detect/image")
    assert resp.status_code == 422


def test_detect_image_deletes_temp_file(client):
    import tempfile
    import os

    before = len(os.listdir(tempfile.gettempdir()))
    _upload(client)
    after = len(os.listdir(tempfile.gettempdir()))
    assert after <= before + 1  # sin acumular archivos temporales


def test_list_detection_verdicts(client):
    resp = client.get("/api/v1/detect/verdicts")
    assert resp.status_code == 200
    codes = {v["code"] for v in resp.json()}
    assert {"autentica", "sospechosa", "manipulada"} <= codes


def test_detection_health(client):
    resp = client.get("/api/v1/detect/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "mock"
    assert body["reachable"] is True


def test_classify_image_thresholds():
    assert classify_image(0.1, 0.05) == ("autentica", 0.1)
    assert classify_image(0.0, 0.29) == ("autentica", 0.29)
    assert classify_image(0.4, 0.2) == ("sospechosa", 0.4)
    assert classify_image(0.55, 0.6) == ("manipulada", 0.6)
    assert classify_image(0.9, 0.1) == ("manipulada", 0.9)


def test_screenshot_filename_is_autentica(client):
    """Capturas de pantalla del SO no deben salir como generadas por IA."""
    # PNG mínimo válido 1x1
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    resp = client.post(
        "/api/v1/detect/image",
        files={
            "file": (
                "Captura de pantalla 2026-08-12 155218.png",
                png,
                "image/png",
            )
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "autentica"
    assert body["risk_score"] < 0.3
    assert "inconsistencias_faciales" not in body["signals"]
    assert body["deepfake_score"] < 0.3


def test_ai_named_image_is_high_risk(client):
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    resp = client.post(
        "/api/v1/detect/image",
        files={"file": ("retrato-midjourney-fake.png", png, "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "manipulada"
    assert body["risk_score"] >= 0.6
