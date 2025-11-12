def register_and_login(client):
    client.post("/register", data={"username": "u", "password": "p"})
    client.post("/login", data={"username": "u", "password": "p"})

def test_crud_inventory(client):
    register_and_login(client)
    # Create
    rv = client.post("/inventory/add", data={"name":"Sardines","category":"Canned","quantity":5,"price":25.5}, follow_redirects=True)
    assert b"Product added" in rv.data
    # Read
    rv = client.get("/inventory")
    assert b"Sardines" in rv.data
    # Update
    rv = client.post("/inventory/1/edit", data={"name":"Sardines","category":"Canned","quantity":7,"price":26.0}, follow_redirects=True)
    assert b"Product updated" in rv.data
    # Delete
    rv = client.post("/inventory/1/delete", follow_redirects=True)
    assert b"Product deleted" in rv.data
