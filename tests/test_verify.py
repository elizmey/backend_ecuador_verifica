def _check(client, claim):
    return client.post("/api/v1/verify/check", json={"claim": claim})


def test_check_known_false_claim(client):
    resp = _check(client, "Las vacunas causan autismo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "falso"
    assert body["verdict_label"] == "Falso"
    assert body["confidence"] >= 0.9
    assert body["explanation"]
    assert body["evidence"]["fact_used"] == "vacunas-autismo"
    assert body["nlp"]["provider"] == "mock"
    assert body["checked_at"]


def test_check_negation_of_false_claim_is_true(client):
    resp = _check(client, "Las vacunas no causan autismo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "verdadero"
    assert body["evidence"]["negation_detected"] is True


def test_check_known_true_claim(client):
    resp = _check(client, "El voto en Ecuador es obligatorio")
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "verdadero"
    assert body["evidence"]["fact_used"] == "voto-obligatorio"


def test_check_misleading_claim(client):
    resp = _check(client, "Los migrantes venezolanos reciben más ayudas que los ecuatorianos")
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "enganyoso"


def test_check_unknown_claim(client):
    resp = _check(client, "Mi vecino observó un ovni ayer sobre la ciudad de Cuenca")
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] in ("sin_evidencia", "enganyoso")
    assert body["evidence"]["fact_used"] is None
    assert body["explanation"]


def test_check_domain_source_matches(client):
    resp = _check(client, "El Ministerio de Salud (salud.gob.ec) anunció una nueva campaña")
    assert resp.status_code == 200
    matches = resp.json()["source_matches"]
    assert any(m["match_type"] == "domain" and m["domain"] == "salud.gob.ec" for m in matches)


def test_check_blank_claim_returns_400(client):
    assert _check(client, "   ").status_code == 400


def test_check_empty_claim_returns_422(client):
    assert _check(client, "").status_code == 422


def test_check_recommended_sources_for_fact(client):
    body = _check(client, "Las vacunas causan autismo").json()
    recommended = body["evidence"]["recommended_sources"]
    assert recommended
    assert all(s["name"] and s["url"] for s in recommended)


def test_list_verdicts(client):
    resp = client.get("/api/v1/verify/verdicts")
    assert resp.status_code == 200
    codes = {v["code"] for v in resp.json()}
    assert {"verdadero", "falso", "enganyoso", "sin_evidencia"} <= codes


def test_list_sources(client):
    resp = client.get("/api/v1/verify/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 10
    assert all(s["domain"] and s["url"] for s in sources)


def test_list_known_claims(client):
    resp = client.get("/api/v1/verify/known-claims")
    assert resp.status_code == 200
    claims = resp.json()
    assert len(claims) >= 8
    assert all(c["verdict"] in ("verdadero", "falso", "enganyoso") for c in claims)
