from app.models.staff import Staff, RoleEnum
from app.core.security import hash_password


def test_create_member(auth_client):
    response = auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    assert response.status_code == 201
    assert response.json()["name"] == "John Doe"


def test_get_member(auth_client):
    created = auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    member_id = created.json()["id"]
    response = auth_client.get(f"/members/{member_id}")
    assert response.status_code == 200
    assert response.json()["id"] == member_id


def test_get_member_not_found(auth_client):
    response = auth_client.get("/members/9999")
    assert response.status_code == 404


def test_duplicate_member(auth_client):
    auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    response = auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    assert response.status_code == 409


def test_update_member(auth_client):
    created = auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    member_id = created.json()["id"]
    response = auth_client.patch(f"/members/{member_id}", json={"name": "Updated Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_delete_member(auth_client):
    created = auth_client.post("/members/", json={
        "name": "John Doe",
        "email": "john@test.com",
        "phone": "123456789",
        "gym_id": 1
    })
    member_id = created.json()["id"]
    response = auth_client.delete(f"/members/{member_id}")
    assert response.status_code == 200
