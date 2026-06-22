import pytest


PRODUCT_DATA = {
    "name": "Test Product",
    "price": 50.00,
    "stock": 20,
}


def create_test_product(client, headers):
    return client.post("/products", json=PRODUCT_DATA, headers=headers).json()


def test_get_empty_cart(client, auth_headers_user):
    resp = client.get("/cart", headers=auth_headers_user)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert float(data["total"]) == 0.0


def test_add_item_to_cart(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    resp = client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=auth_headers_user)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert float(data["total"]) == 100.0


def test_add_item_insufficient_stock(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    # stock=20, quantity=25 is valid per schema (≤99) but exceeds stock
    resp = client.post("/cart/items", json={"product_id": product["id"], "quantity": 25}, headers=auth_headers_user)
    assert resp.status_code == 400


def test_add_item_cumulates(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=auth_headers_user)
    resp = client.post("/cart/items", json={"product_id": product["id"], "quantity": 3}, headers=auth_headers_user)
    assert resp.json()["items"][0]["quantity"] == 5


def test_update_cart_item(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=auth_headers_user)
    resp = client.put(f"/cart/items/{product['id']}", json={"quantity": 5}, headers=auth_headers_user)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["quantity"] == 5


def test_remove_cart_item(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1}, headers=auth_headers_user)
    resp = client.delete(f"/cart/items/{product['id']}", headers=auth_headers_user)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_clear_cart(client, auth_headers_user, auth_headers_admin):
    product = create_test_product(client, auth_headers_admin)
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=auth_headers_user)
    resp = client.delete("/cart", headers=auth_headers_user)
    assert resp.status_code == 200
    assert float(resp.json()["total"]) == 0.0


def test_cart_requires_auth(client):
    resp = client.get("/cart")
    assert resp.status_code in (401, 403)
