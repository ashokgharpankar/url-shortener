TARGET = "https://example.com/some/page"


def test_shorten_returns_short_url(client):
    resp = client.post("/shorten", json={"target_url": TARGET})

    assert resp.status_code == 201
    data = resp.json()
    assert data["target_url"] == TARGET
    assert len(data["code"]) == 7
    assert data["short_url"].endswith("/" + data["code"])
    assert data["clicks"] == 0


def test_shorten_rejects_invalid_url(client):
    resp = client.post("/shorten", json={"target_url": "not a url"})
    assert resp.status_code == 422


def test_redirect_to_target(client):
    code = client.post("/shorten", json={"target_url": TARGET}).json()["code"]

    # Don't follow the redirect; we want to inspect it.
    resp = client.get(f"/{code}", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == TARGET


def test_unknown_code_returns_404(client):
    resp = client.get("/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


def test_code_collision_retries(client, monkeypatch):
    # Force a collision: first link gets "dup1", second link's first
    # attempt also gets "dup1", then "dup2" on retry.
    codes = iter(["dup1", "dup1", "dup2"])
    monkeypatch.setattr("app.crud.generate_code", lambda length: next(codes))

    first = client.post("/shorten", json={"target_url": TARGET}).json()
    second = client.post("/shorten", json={"target_url": TARGET}).json()

    assert first["code"] == "dup1"
    assert second["code"] == "dup2"

def test_stats_counts_clicks(client):
    code = client.post("/shorten", json={"target_url": TARGET}).json()["code"]

    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)

    resp = client.get(f"/stats/{code}")
    assert resp.status_code == 200
    assert resp.json()["clicks"] == 2


def test_stats_unknown_code_returns_404(client):
    resp = client.get("/stats/doesnotexist")
    assert resp.status_code == 404
