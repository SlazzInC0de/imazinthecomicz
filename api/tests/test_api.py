import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


@pytest.fixture()
def client(catalog):
    settings = Settings(allowed_origins=["https://web.example"], proxy_key="s3cret", rate_per_minute=600,
                        rate_burst=100)
    with TestClient(create_app(settings, catalog)) as c:
        yield c


def test_health_and_headers(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"ok": True, "titles": 6, "mode": "hybrid"}
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_search_returns_cards_with_match_info(client):
    r = client.get("/api/search", params={"q": "detective ghosts", "limit": 2})
    body = r.json()
    assert r.status_code == 200 and body["mode"] == "hybrid" and len(body["results"]) == 2
    top = body["results"][0]
    assert top["id"] == "al-1" and top["match"]["label"] in {"strong", "good", "loose"}
    assert "doc" not in top and "description" not in top


def test_search_filters_and_validation(client):
    r = client.get("/api/search", params=[("q", "story"), ("kind", "Manhwa")])
    assert [c["id"] for c in r.json()["results"]] == ["al-3"]
    assert client.get("/api/search", params={"q": ""}).status_code == 422
    assert client.get("/api/search", params={"q": "x" * 201}).status_code == 422
    assert client.get("/api/search", params={"q": "a", "kind": "Novel"}).status_code == 422
    assert client.get("/api/search", params={"q": "a", "tone": 2}).status_code == 422
    assert client.get("/api/search", params={"q": "a", "limit": 500}).status_code == 422
    assert client.get("/api/search", params={"q": "a", "year_min": 2020, "year_max": 2000}).status_code == 422
    assert client.get("/api/search", params={"q": "a", "genre": "x" * 41}).status_code == 422


def test_search_handles_injection_style_input(client):
    for q in ["'; DROP TABLE comics; --", "<script>alert(1)</script>", "../../etc/passwd", "{{7*7}}"]:
        r = client.get("/api/search", params={"q": q})
        assert r.status_code == 200
        assert "<script>" not in r.text.replace(r.json()["query"], "")


def test_comic_detail_and_404(client):
    r = client.get("/api/comics/al-3")
    assert r.status_code == 200 and r.json()["title"] == "Star Fleet Academy"
    assert client.get("/api/comics/al-999").status_code == 404
    assert client.get("/api/comics/../etc").status_code == 404
    assert client.get("/api/comics/drop-table").status_code == 422


def test_similar(client):
    r = client.get("/api/comics/al-1/similar", params={"limit": 3})
    got = [c["id"] for c in r.json()["results"]]
    assert r.status_code == 200 and "al-1" not in got and len(got) == 3


def test_browse_and_facets_and_ids(client):
    assert client.get("/api/browse", params={"sort": "score", "limit": 1}).json()["results"][0]["id"] == "al-5"
    assert client.get("/api/browse", params={"sort": "random"}).status_code == 422
    assert client.get("/api/facets").json()["total"] == 6
    assert client.get("/api/ids", params={"limit": 2}).json()["ids"] == ["al-1", "al-3"]


def test_cors_only_for_allowed_origin(client):
    ok = client.get("/api/health", headers={"Origin": "https://web.example"})
    bad = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "https://web.example"
    assert "access-control-allow-origin" not in bad.headers


def test_only_get_is_allowed(client):
    assert client.post("/api/search", params={"q": "x"}).status_code == 405


def test_docs_hidden_by_default(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_rate_limit_per_visitor(catalog):
    settings = Settings(proxy_key="s3cret", rate_per_minute=1, rate_burst=2)
    with TestClient(create_app(settings, catalog)) as c:
        visitor = {"X-Proxy-Key": "s3cret", "X-Client-IP": "1.1.1.1"}
        assert [c.get("/api/health", headers=visitor).status_code for _ in range(3)] == [200, 200, 429]
        # a different visitor behind the same server still gets through
        other = {"X-Proxy-Key": "s3cret", "X-Client-IP": "2.2.2.2"}
        assert c.get("/api/health", headers=other).status_code == 200
        # a spoofed IP without the key is limited by the real connection instead
        spoof = {"X-Client-IP": "3.3.3.3"}
        codes = [c.get("/api/health", headers=spoof).status_code for _ in range(3)]
        assert codes[-1] == 429
        assert "retry-after" in c.get("/api/health", headers=spoof).headers
        # the web server's cached renders (key, no visitor) are not limited
        server = {"X-Proxy-Key": "s3cret"}
        assert {c.get("/api/health", headers=server).status_code for _ in range(5)} == {200}
        # a wrong key does not unlock that
        wrong = {"X-Proxy-Key": "guess", "X-Client-IP": "4.4.4.4"}
        assert [c.get("/api/health", headers=wrong).status_code for _ in range(2)][-1] == 429
