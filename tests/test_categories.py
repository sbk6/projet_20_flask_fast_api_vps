import pytest
from app.models.category import Category


def test_list_categories_empty(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_category_admin(client, auth_headers_admin, db):
    resp = client.post("/categories", json={
        "name": "Électronique",
        "description": "High-tech",
    }, headers=auth_headers_admin)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Électronique"
    assert data["slug"] == "electronique"


def test_create_category_forbidden_for_client(client, auth_headers_user):
    resp = client.post("/categories", json={"name": "Test"}, headers=auth_headers_user)
    assert resp.status_code == 403


def test_create_category_no_auth(client):
    resp = client.post("/categories", json={"name": "Test"})
    assert resp.status_code in (401, 403)


def test_get_category(client, auth_headers_admin):
    create = client.post("/categories", json={"name": "Mode"}, headers=auth_headers_admin)
    cat_id = create.json()["id"]
    resp = client.get(f"/categories/{cat_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Mode"


def test_get_category_not_found(client):
    resp = client.get("/categories/9999")
    assert resp.status_code == 404


def test_update_category(client, auth_headers_admin):
    create = client.post("/categories", json={"name": "Sport"}, headers=auth_headers_admin)
    cat_id = create.json()["id"]
    resp = client.put(f"/categories/{cat_id}", json={"description": "Articles de sport"}, headers=auth_headers_admin)
    assert resp.status_code == 200
    assert resp.json()["description"] == "Articles de sport"


def test_delete_category(client, auth_headers_admin):
    create = client.post("/categories", json={"name": "Temp"}, headers=auth_headers_admin)
    cat_id = create.json()["id"]
    resp = client.delete(f"/categories/{cat_id}", headers=auth_headers_admin)
    assert resp.status_code == 204
    resp2 = client.get(f"/categories/{cat_id}")
    assert resp2.status_code == 404
