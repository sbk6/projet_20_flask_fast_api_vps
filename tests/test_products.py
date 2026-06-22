import pytest


PRODUCT_DATA = {
    "name": "iPhone 15 Pro",
    "description": "Smartphone Apple",
    "price": 1199.99,
    "stock": 30,
    "image_url": "https://example.com/iphone.jpg",
}


def create_product(client, headers, data=None):
    return client.post("/products", json=data or PRODUCT_DATA, headers=headers)


def test_list_products_empty(client):
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


def test_create_product_admin(client, auth_headers_admin):
    resp = create_product(client, auth_headers_admin)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "iPhone 15 Pro"
    assert float(data["price"]) == 1199.99
    assert data["stock"] == 30


def test_create_product_forbidden(client, auth_headers_user):
    resp = create_product(client, auth_headers_user)
    assert resp.status_code == 403


def test_create_product_negative_price(client, auth_headers_admin):
    resp = create_product(client, auth_headers_admin, {**PRODUCT_DATA, "price": -10})
    assert resp.status_code == 422


def test_create_product_negative_stock(client, auth_headers_admin):
    resp = create_product(client, auth_headers_admin, {**PRODUCT_DATA, "stock": -5})
    assert resp.status_code == 422


def test_get_product_detail(client, auth_headers_admin):
    create = create_product(client, auth_headers_admin)
    prod_id = create.json()["id"]
    resp = client.get(f"/products/{prod_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Smartphone Apple"
    assert data["review_count"] == 0
    assert data["average_rating"] is None


def test_get_product_not_found(client):
    resp = client.get("/products/9999")
    assert resp.status_code == 404


def test_filter_by_price(client, auth_headers_admin):
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "price": 100.00, "name": "Cheap"})
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "price": 2000.00, "name": "Expensive"})
    resp = client.get("/products?price_max=500")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(float(p["price"]) <= 500 for p in items)


def test_filter_by_search(client, auth_headers_admin):
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "name": "Samsung Galaxy S25"})
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "name": "Apple Watch Ultra"})
    resp = client.get("/products?search=Samsung")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Samsung" in p["name"] for p in items)


def test_filter_in_stock(client, auth_headers_admin):
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "name": "In Stock", "stock": 10})
    create_product(client, auth_headers_admin, {**PRODUCT_DATA, "name": "Out Stock", "stock": 0})
    resp = client.get("/products?in_stock=true")
    items = resp.json()["items"]
    assert all(p["stock"] > 0 for p in items)


def test_update_product(client, auth_headers_admin):
    create = create_product(client, auth_headers_admin)
    prod_id = create.json()["id"]
    resp = client.put(f"/products/{prod_id}", json={"price": 999.99, "stock": 15}, headers=auth_headers_admin)
    assert resp.status_code == 200
    assert float(resp.json()["price"]) == 999.99


def test_delete_product_soft(client, auth_headers_admin):
    create = create_product(client, auth_headers_admin)
    prod_id = create.json()["id"]
    resp = client.delete(f"/products/{prod_id}", headers=auth_headers_admin)
    assert resp.status_code == 204
    resp2 = client.get(f"/products/{prod_id}")
    assert resp2.status_code == 404


def test_pagination(client, auth_headers_admin):
    for i in range(5):
        create_product(client, auth_headers_admin, {**PRODUCT_DATA, "name": f"Product {i}"})
    resp = client.get("/products?page=1&size=3")
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["pages"] == 2
