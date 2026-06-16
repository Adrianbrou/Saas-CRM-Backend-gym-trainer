"""
workout_repository.py

Repository layer for Workout.
Handles all direct database operations — no business logic lives here.
Workouts are NOT gym-scoped: they are shared across all gyms.
"""

from sqlalchemy.orm import Session
from app.models.workout import Workout
from typing import List


def create(db: Session, workout: Workout) -> Workout:
    """Persist a new Workout to the database.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout: A Workout model instance (not yet committed).

    Returns:
        The saved Workout with its database-generated id populated.
    """
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def get_by_id(db: Session, workout_id: int) -> Workout | None:
    """Fetch a single Workout by its primary key.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to retrieve.

    Returns:
        The matching Workout, or None if not found.
    """
    return db.query(Workout).filter(Workout.id == workout_id).first()


def get_by_name(db: Session, name: str) -> Workout | None:
    """Fetch a single Workout by its unique name.

    Used by the service layer for the duplicate-name check, so that business logic
    never has to issue a raw query itself.

    Args:
        db: SQLAlchemy session injected by the caller.
        name: The workout name to look up.

    Returns:
        The matching Workout, or None if no workout has that name.
    """
    return db.query(Workout).filter(Workout.name == name).first()


def get_by_body_part(db: Session, body_part_id: int) -> List[Workout]:
    """Fetch all Workouts belonging to a specific body part.

    Args:
        db: SQLAlchemy session injected by the caller.
        body_part_id: Primary key of the BodyPart to filter by.

    Returns:
        A list of Workouts for that body part (empty list if none exist).
    """
    return db.query(Workout).filter(Workout.body_part_id == body_part_id).all()


def get_all(db: Session, skip: int = 0, limit: int = 20) -> List[Workout]:
    """Fetch all Workouts in the database.

    Workouts are not tenant-scoped, so no gym_id filter is needed.

    Args:
        db: SQLAlchemy session injected by the caller.

    Returns:
        A list of all Workouts (empty list if none exist).
    """
    return db.query(Workout).offset(skip).limit(limit).all()


def update(db: Session, workout_id: int, updates: dict) -> Workout | None:
    """Apply a partial update to an existing Workout.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to update.
        updates: Dictionary of field names to new values (e.g. {"name": "Squat"}).

    Returns:
        The updated Workout, or None if the workout was not found.
    """
    workout = get_by_id(db, workout_id)
    if not workout:
        return None

    for key, value in updates.items():
        setattr(workout, key, value)

    db.commit()
    db.refresh(workout)

    return workout


def delete(db: Session, workout_id: int) -> bool:
    """Delete a Workout by its primary key.

    Args:
        db: SQLAlchemy session injected by the caller.
        workout_id: Primary key of the workout to delete.

    Returns:
        True if the workout was found and deleted, False if not found.
    """
    workout = get_by_id(db, workout_id)
    if not workout:
        return False
    db.delete(workout)
    db.commit()

    return True
