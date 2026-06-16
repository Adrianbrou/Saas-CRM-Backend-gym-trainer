def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_get_gym(auth_client):
    created = auth_client.post(
        "/gyms/", json={"name": "Gym2", "location": "City2"})
    gym_id = created.json()["id"]
    response = auth_client.get(f"/gyms/{gym_id}")
    assert response.status_code == 200
    assert response.json()["id"] == gym_id


def test_api_get_gym_not_found(auth_client):
    response = auth_client.get("/gyms/9999")
    assert response.status_code == 404


def test_api_duplicate_gym(client):
    client.post("/gyms/", json={"name": "Test Gym", "location": "Test City"})
    response = client.post(
        "/gyms/", json={"name": "Test Gym", "location": "Test City"})
    assert response.status_code == 409


def test_api_update_gym(auth_client):
    created = auth_client.post(
        "/gyms/", json={"name": "Gym2", "location": "City2"})
    gym_id = created.json()["id"]
    response = auth_client.patch(
        f"/gyms/{gym_id}", json={"name": "Updated Gym"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Gym"


def test_api_delete_gym(auth_client):
    created = auth_client.post(
        "/gyms/", json={"name": "Gym2", "location": "City2"})
    gym_id = created.json()["id"]
    response = auth_client.delete(f"/gyms/{gym_id}")
    assert response.status_code == 200
