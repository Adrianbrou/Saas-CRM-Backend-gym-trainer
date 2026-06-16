"""
workouts.py — Workouts API Router

Handles all HTTP endpoints for Workout resources.
Workouts are NOT gym-scoped — they are shared across all gyms.
A workout must be linked to an existing BodyPart (e.g. Chest, Legs).
Workout names must be unique system-wide.

Route summary:
    POST   /workouts/               → create a new workout
    GET    /workouts/               → list all workouts in the system
    GET    /workouts/{workout_id}   → retrieve one workout by id
    PATCH  /workouts/{workout_id}   → partially update a workout
    DELETE /workouts/{workout_id}   → remove a workout

Error handling:
    ValueError from service layer → 400 Bad Request (duplicate name or not found)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import workout_service
from app.schemas.workout import WorkoutCreate, WorkoutResponse, WorkoutUpdate
from app.core.dependency import get_current_user, require_manager


router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post(
    "/",
    response_model=WorkoutResponse,
    summary="Create a new workout",
    description=(
        "Creates a new workout linked to an existing body part. "
        "Workout names must be unique across the entire system — "
        "workouts are shared between all gyms, not scoped per gym."
    ), status_code=201,
)
def create_workout(data: WorkoutCreate, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Create a new workout.

    Args:
        data: WorkoutCreate schema — name, body_part_id.
        db: Database session injected by FastAPI.

    Returns:
        WorkoutResponse: The newly created workout including id and timestamps.

    Raises:
        HTTPException 400: If a workout with that name already exists.
    """
    return workout_service.create_workout(db, data)


@router.get(
    "/",
    response_model=list[WorkoutResponse],
    summary="List all workouts",
    description="Returns every workout in the system. Workouts are shared across all gyms.",
)
def get_all(_=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all workouts in the system.

    Args:
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[WorkoutResponse]: All workouts (may be empty).
    """
    return workout_service.get_all(db, skip=skip, limit=limit)


@router.get(
    "/{workout_id}",
    response_model=WorkoutResponse,
    summary="Get a workout by id",
    description="Returns a single workout identified by its primary key.",
)
def get_workout(workout_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve one workout by primary key.

    Args:
        workout_id: Primary key of the workout to retrieve.
        db: Database session injected by FastAPI.

    Returns:
        WorkoutResponse: The matching workout.

    Raises:
        HTTPException 400: If no workout with that id exists.
    """
    return workout_service.get_workout(db, workout_id)


@router.patch(
    "/{workout_id}",
    response_model=WorkoutResponse,
    summary="Update a workout",
    description="Partially updates a workout. Only send the fields you want to change.",
)
def update_workout(workout_id: int, data: WorkoutUpdate, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Partially update a workout's fields.

    Args:
        workout_id: Primary key of the workout to update.
        data: WorkoutUpdate schema — all fields optional (name, body_part_id).
        db: Database session injected by FastAPI.

    Returns:
        WorkoutResponse: The updated workout with new values reflected.

    Raises:
        HTTPException 400: If no workout with that id exists.
    """
    return workout_service.update_workout(db, workout_id, data)


@router.delete(
    "/{workout_id}",
    response_model=bool,
    summary="Delete a workout",
    description="Permanently removes a workout from the system. Returns True on success.",
)
def delete_workout(workout_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Delete a workout by primary key.

    Args:
        workout_id: Primary key of the workout to delete.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the workout was found and deleted.

    Raises:
        HTTPException 400: If no workout with that id exists.
    """
    return workout_service.delete_workout(db, workout_id)
