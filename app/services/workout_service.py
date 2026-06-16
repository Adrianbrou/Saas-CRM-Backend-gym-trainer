"""
workout_service.py — Business Logic for Workout and BodyPart

Workouts are NOT gym-scoped — they are shared across all gyms.
A workout must be linked to an existing BodyPart (e.g. Chest, Legs).
Workout names must be unique across the entire system.
"""

from app.models.workout import Workout
from app.repository import workout_repository
from app.schemas.workout import WorkoutCreate, WorkoutUpdate, WorkoutResponse
from sqlalchemy.orm import Session
from app.core import cache
from app.core.exceptions import NotFoundError, DuplicateError


def create_workout(db: Session, data: WorkoutCreate) -> Workout:
    """Create a new workout after verifying the name is not already taken.

    Business rules enforced:
      - Workout names must be unique system-wide (not per gym)

    Args:
        db: SQLAlchemy session injected by the caller.
        data: Validated WorkoutCreate schema (name, body_part_id).

    Raises:
        ValueError: If a workout with the same name already exists.

    Returns:
        The newly created Workout with database-generated id.
    """
    # Check duplicate name via the repository - workouts are global, names must be unique.
    # The query lives in the repository so the service never touches SQLAlchemy directly.
    existing = workout_repository.get_by_name(db, data.name)
    if existing:
        raise DuplicateError("Workout with this name already exists")

    workout = Workout(**data.model_dump())
    return workout_repository.create(db, workout)


def get_workout(db: Session, workout_id: int) -> WorkoutResponse:
    """Retrieve a workout by id after verifying it exists.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to retrieve.

    Raises:
        ValueError: If no workout with that id exists.

    Returns:
        The matching Workout object.
    """
    # Return a validated WorkoutResponse on both the cache-hit and cache-miss paths.
    cached = cache.redis_client.get(f"workout:{workout_id}")
    if cached and isinstance(cached, str):
        return WorkoutResponse.model_validate_json(cached)

    existing = workout_repository.get_by_id(db, workout_id)
    if not existing:
        raise NotFoundError("Workout not found")
    response = WorkoutResponse.model_validate(existing)
    cache.redis_client.set(f"workout:{workout_id}", response.model_dump_json(), ex=300)
    return response


def get_all(db: Session, skip: int = 0, limit: int = 20) -> list[Workout]:
    """this function is the retrieve the all Workouts information  from the db
    Args:
        db (Session): Session to the database
        skip (int): Number of records to skip. Defaults to 0.
        limit (int): Maximum number of records to return. Defaults to 20.

    Returns:
        all Workouts found as list
    """

    return workout_repository.get_all(db, skip=skip, limit=limit)


def update_workout(db: Session, workout_id: int, data: WorkoutUpdate) -> Workout:
    """Update an existing workout's fields after verifying it exists.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to update.
        data: Validated WorkoutUpdate schema — all fields optional.

    Raises:
        ValueError: If no workout with that id exists.

    Returns:
        The updated Workout with new values reflected.
    """
    existing = workout_repository.get_by_id(db, workout_id)
    if not existing:
        raise NotFoundError("Workout not found")

    # Only update fields the client actually sent
    updates = data.model_dump(exclude_unset=True)
    result = workout_repository.update(db, workout_id, updates)
    cache.redis_client.delete(f"workout:{workout_id}")
    return result


def delete_workout(db: Session, workout_id: int) -> bool:
    """Delete a workout after verifying it exists.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to delete.

    Raises:
        ValueError: If no workout with that id exists.

    Returns:
        True if the workout was found and deleted.
    """
    existing = workout_repository.get_by_id(db, workout_id)
    if not existing:
        raise NotFoundError("Workout not found")
    workout_repository.delete(db, workout_id)
    cache.redis_client.delete(f"workout:{workout_id}")
    return True
