TARGET = "https://example.com/some/page"


def test_home_page_renders_form(client):
    resp = client.get("/")

    assert resp.status_code == 200
    assert '<form method="post"' in resp.text


def test_form_creates_short_link(client):
    # data= sends a form submission, json= sends JSON.
    resp = client.post("/", data={"target_url": TARGET, "alias": "ui-link"})

    assert resp.status_code == 200
    assert "/ui-link" in resp.text
    assert client.get("/ui-link", follow_redirects=False).status_code == 307


def test_form_shows_error_for_invalid_url(client):
    resp = client.post("/", data={"target_url": "not a url", "alias": ""})

    assert resp.status_code == 422
    assert 'class="error"' in resp.text


def test_form_shows_error_for_taken_alias(client):
    client.post("/", data={"target_url": TARGET, "alias": "dup"})
    resp = client.post("/", data={"target_url": TARGET, "alias": "dup"})

    assert resp.status_code == 409
    assert "already in use" in resp.text
