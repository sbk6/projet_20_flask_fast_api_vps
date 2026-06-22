import pytest

PRODUCT_DATA = {"name": "Order Product", "price": 100.00, "stock": 50}
SHIPPING = {"shipping_address": "12 Rue de la Paix, 75001 Paris, France"}


def setup_cart(client, admin_headers, user_headers):
    product = client.post("/products", json=PRODUCT_DATA, headers=admin_headers).json()
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=user_headers)
    return product


def test_create_order(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    resp = client.post("/orders", json=SHIPPING, headers=auth_headers_user)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert float(data["total_price"]) == 200.0
    assert len(data["items"]) == 1


def test_create_order_empty_cart(client, auth_headers_user):
    resp = client.post("/orders", json=SHIPPING, headers=auth_headers_user)
    assert resp.status_code == 400


def test_cart_cleared_after_order(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    client.post("/orders", json=SHIPPING, headers=auth_headers_user)
    cart = client.get("/cart", headers=auth_headers_user).json()
    assert cart["items"] == []


def test_list_orders(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    client.post("/orders", json=SHIPPING, headers=auth_headers_user)
    resp = client.get("/orders", headers=auth_headers_user)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_order_detail(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    order = client.post("/orders", json=SHIPPING, headers=auth_headers_user).json()
    resp = client.get(f"/orders/{order['id']}", headers=auth_headers_user)
    assert resp.status_code == 200


def test_cancel_pending_order(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    order = client.post("/orders", json=SHIPPING, headers=auth_headers_user).json()
    resp = client.put(f"/orders/{order['id']}/cancel", headers=auth_headers_user)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


def test_admin_change_order_status(client, auth_headers_user, auth_headers_admin):
    setup_cart(client, auth_headers_admin, auth_headers_user)
    order = client.post("/orders", json=SHIPPING, headers=auth_headers_user).json()
    resp = client.put(f"/orders/{order['id']}/status", json={"status": "confirmed"}, headers=auth_headers_admin)
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


def test_order_requires_auth(client):
    resp = client.get("/orders")
    assert resp.status_code in (401, 403)
