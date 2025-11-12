def test_redirect_to_login(client):
    rv = client.get("/", follow_redirects=True)
    assert b"Login" in rv.data
