def test_chat_basic_greeting(client):
    resp = client.post("/api/v1/chat", json={"message": "hola"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] in ("basic", "gemini", "knowledge")
    assert body["reply"]


def test_chat_sources_question(client):
    resp = client.post("/api/v1/chat", json={"message": "¿Qué fuentes son confiables?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] in ("basic", "gemini", "knowledge")
    assert body["reply"]


def test_chat_requires_message(client):
    assert client.post("/api/v1/chat", json={"message": ""}).status_code == 422
