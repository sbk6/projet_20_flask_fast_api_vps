import pytest

PRODUCT_DATA = {"name": "Review Product", "price": 25.00, "stock": 10}
REVIEW_DATA = {"rating": 5, "title": "Excellent !", "comment": "Très satisfait."}


def create_product(client, admin_headers):
    return client.post("/products", json=PRODUCT_DATA, headers=admin_headers).json()


def test_list_reviews_empty(client, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    resp = client.get(f"/products/{product['id']}/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


def test_post_review(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    resp = client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA, headers=auth_headers_user)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5
    assert data["username"] == "testuser"


def test_post_review_invalid_rating(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    resp = client.post(f"/products/{product['id']}/reviews", json={"rating": 6}, headers=auth_headers_user)
    assert resp.status_code == 422


def test_post_review_duplicate(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA, headers=auth_headers_user)
    resp = client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA, headers=auth_headers_user)
    assert resp.status_code == 409


def test_post_review_nonexistent_product(client, auth_headers_user):
    resp = client.post("/products/9999/reviews", json=REVIEW_DATA, headers=auth_headers_user)
    assert resp.status_code == 404


def test_update_review(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    review = client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA, headers=auth_headers_user).json()
    resp = client.put(f"/reviews/{review['id']}", json={"rating": 4, "comment": "Bien mais peut mieux faire."}, headers=auth_headers_user)
    assert resp.status_code == 200
    assert resp.json()["rating"] == 4


def test_delete_review_by_author(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    review = client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA, headers=auth_headers_user).json()
    resp = client.delete(f"/reviews/{review['id']}", headers=auth_headers_user)
    assert resp.status_code == 204


def test_product_stats_after_review(client, auth_headers_user, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    client.post(f"/products/{product['id']}/reviews", json={"rating": 4}, headers=auth_headers_user)
    detail = client.get(f"/products/{product['id']}").json()
    assert detail["review_count"] == 1
    assert detail["average_rating"] == 4.0


def test_review_requires_auth(client, auth_headers_admin):
    product = create_product(client, auth_headers_admin)
    resp = client.post(f"/products/{product['id']}/reviews", json=REVIEW_DATA)
    assert resp.status_code in (401, 403)
