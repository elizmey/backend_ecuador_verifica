def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "veriia-ecuador-backend"


def test_swagger_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_spec(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec["info"]["title"] == "VeriIA Ecuador API"
    assert "/api/v1/auth/login" in spec["paths"]
    assert "/api/v1/requests" in spec["paths"]
    assert "/api/v1/ai/nlp" in spec["paths"]
