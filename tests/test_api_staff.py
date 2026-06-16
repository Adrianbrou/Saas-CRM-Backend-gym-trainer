from app.models.staff import Staff, RoleEnum
from app.core.security import hash_password
from tests.conftest import TestingSessionLocal


def test_create_staff(auth_client):
    # auth_client already has a manager — create a second staff member
    response = auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Trainer One"


def test_get_staff(auth_client):
    created = auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    staff_id = created.json()["id"]
    response = auth_client.get(f"/staff/{staff_id}")
    assert response.status_code == 200
    assert response.json()["id"] == staff_id


def test_get_staff_not_found(auth_client):
    response = auth_client.get("/staff/9999")
    assert response.status_code == 404


def test_duplicate_staff(auth_client):
    auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    response = auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    assert response.status_code == 409


def test_update_staff(auth_client):
    created = auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    staff_id = created.json()["id"]
    response = auth_client.patch(f"/staff/{staff_id}", json={"name": "Updated Trainer"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Trainer"


def test_delete_staff(auth_client):
    created = auth_client.post("/staff/", json={
        "name": "Trainer One",
        "email": "trainer@test.com",
        "phone": "987654321",
        "role": "trainer",
        "gym_id": 1,
        "password": "pass123"
    })
    staff_id = created.json()["id"]
    response = auth_client.delete(f"/staff/{staff_id}")
    assert response.status_code == 200
