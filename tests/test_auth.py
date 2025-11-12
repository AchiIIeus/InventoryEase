def register(client, username="user1", password="pass123"):
    return client.post("/register", data={"username": username, "password": password}, follow_redirects=True)

def login(client, username="user1", password="pass123"):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

def test_register_and_login_flow(client):
    rv = register(client)
    assert b"Registration successful" in rv.data
    rv = login(client)
    assert b"Dashboard" in rv.data
