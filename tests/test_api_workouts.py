from app.models.workout import BodyPart
from tests.conftest import TestingSessionLocal


def _seed_body_part(name="Chest"):
    """Seed a BodyPart directly into the test DB — no API endpoint exists for this."""
    db = TestingSessionLocal()
    body_part = BodyPart(name=name)
    db.add(body_part)
    db.commit()
    db.refresh(body_part)
    db.close()
    return body_part.id


def test_create_workout(auth_client):
    body_part_id = _seed_body_part()
    response = auth_client.post("/workouts/", json={
        "name": "Bench Press",
        "body_part_id": body_part_id
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Bench Press"


def test_get_workout(auth_client):
    body_part_id = _seed_body_part()
    created = auth_client.post("/workouts/", json={
        "name": "Bench Press",
        "body_part_id": body_part_id
    })
    workout_id = created.json()["id"]
    response = auth_client.get(f"/workouts/{workout_id}")
    assert response.status_code == 200
    assert response.json()["id"] == workout_id


def test_get_workout_not_found(auth_client):
    response = auth_client.get("/workouts/9999")
    assert response.status_code == 404


def test_duplicate_workout(auth_client):
    body_part_id = _seed_body_part()
    auth_client.post("/workouts/", json={"name": "Bench Press", "body_part_id": body_part_id})
    response = auth_client.post("/workouts/", json={"name": "Bench Press", "body_part_id": body_part_id})
    assert response.status_code == 409


def test_update_workout(auth_client):
    body_part_id = _seed_body_part()
    created = auth_client.post("/workouts/", json={
        "name": "Bench Press",
        "body_part_id": body_part_id
    })
    workout_id = created.json()["id"]
    response = auth_client.patch(f"/workouts/{workout_id}", json={"name": "Incline Press"})
    assert response.status_code == 200
    assert response.json()["name"] == "Incline Press"


def test_delete_workout(auth_client):
    body_part_id = _seed_body_part()
    created = auth_client.post("/workouts/", json={
        "name": "Bench Press",
        "body_part_id": body_part_id
    })
    workout_id = created.json()["id"]
    response = auth_client.delete(f"/workouts/{workout_id}")
    assert response.status_code == 200
