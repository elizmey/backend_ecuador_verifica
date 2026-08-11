def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["storage"] == "memory"


def test_swagger_docs(client):
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()


def test_openapi_exposes_verify_check(client):
    spec = client.get("/openapi.json").json()
    assert "/api/v1/verify/check" in spec["paths"]
