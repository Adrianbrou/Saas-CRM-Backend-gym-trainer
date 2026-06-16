"""
progress.py — Progress API Router

Handles all HTTP endpoints for Progress resources.
Progress records track a member's performance per workout per session
(weight lifted, sets, reps). Records are not gym-scoped but are linked to
a member, a workout, and a workout session via foreign keys.

Route summary:
    POST   /progress/                           → log a new progress record
    GET    /progress/                           → list all progress records
    GET    /progress/{progress_id}              → retrieve one record by id
    PATCH  /progress/{progress_id}              → partially update a record
    DELETE /progress/{progress_id}              → remove a record
    GET    /progress/member/{member_id}         → all records for a member
    GET    /progress/workout/{workout_id}        → all records for a workout
    GET    /progress/session/{session_id}        → all records from a session

Error handling:
    ValueError from service layer → 400 Bad Request (not found)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import progress_service
from app.schemas.progress import ProgressCreate, ProgressResponse, ProgressUpdate
from app.core.dependency import get_current_user


router = APIRouter(prefix="/progress", tags=["progress"])


@router.post(
    "/",
    response_model=ProgressResponse,
    summary="Log a new progress record",
    description=(
        "Creates a progress record linking a member's performance to a specific "
        "workout and session. All three foreign keys (member_id, workout_id, "
        "workout_session_id) are required."
    ), status_code=201,
)
def log_progress(data: ProgressCreate, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Log a new progress record for a member.

    Args:
        data: ProgressCreate schema — member_id, workout_id, workout_session_id,
              weight_kg, sets, reps.
        db: Database session injected by FastAPI.

    Returns:
        ProgressResponse: The newly created progress record including id and logged_at.
    """
    return progress_service.log_progress(db, data)


@router.get(
    "/member/{member_id}",
    response_model=list[ProgressResponse],
    summary="Get all progress records for a member",
    description="Returns every progress record logged for the given member.",
)
def get_by_member(member_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all progress records for a specific member.

    Args:
        member_id: Primary key of the member.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[ProgressResponse]: All progress records for that member (may be empty).
    """
    return progress_service.get_progress_by_member(db, member_id, skip=skip, limit=limit)


@router.get(
    "/workout/{workout_id}",
    response_model=list[ProgressResponse],
    summary="Get all progress records for a workout",
    description="Returns every progress record logged for the given workout across all members.",
)
def get_by_workout(workout_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all progress records for a specific workout.

    Args:
        workout_id: Primary key of the workout.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[ProgressResponse]: All progress records for that workout (may be empty).
    """
    return progress_service.get_progress_by_workout(db, workout_id, skip=skip, limit=limit)


@router.get(
    "/session/{session_id}",
    response_model=list[ProgressResponse],
    summary="Get all progress records from a session",
    description="Returns every progress record logged during the given workout session.",
)
def get_by_session(session_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all progress records logged in a specific workout session.

    Args:
        session_id: Primary key of the workout session.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[ProgressResponse]: All progress records from that session (may be empty).
    """
    return progress_service.get_progress_by_session(db, session_id, skip=skip, limit=limit)


@router.get(
    "/",
    response_model=list[ProgressResponse],
    summary="List all progress records",
    description="Returns every progress record in the system.",
)
def get_all(_=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all progress records in the system.

    Args:
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[ProgressResponse]: All progress records (may be empty).
    """
    return progress_service.get_all(db, skip=skip, limit=limit)


@router.get(
    "/{progress_id}",
    response_model=ProgressResponse,
    summary="Get a progress record by id",
    description="Returns a single progress record identified by its primary key.",
)
def get_progress(progress_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve one progress record by primary key.

    Args:
        progress_id: Primary key of the progress record.
        db: Database session injected by FastAPI.

    Returns:
        ProgressResponse: The matching progress record.

    Raises:
        HTTPException 400: If no record with that id exists.
    """
    return progress_service.get_progress(db, progress_id)


@router.patch(
    "/{progress_id}",
    response_model=ProgressResponse,
    summary="Update a progress record",
    description=(
        "Partially updates a progress record. Only performance values can be changed "
        "(weight_kg, sets, reps). Foreign keys (member_id, workout_id, workout_session_id) "
        "are not updatable — delete and recreate if the wrong references were used."
    ),
)
def update_progress(progress_id: int, data: ProgressUpdate, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Partially update a progress record.

    Args:
        progress_id: Primary key of the record to update.
        data: ProgressUpdate schema — all fields optional (weight_kg, sets, reps).
        db: Database session injected by FastAPI.

    Returns:
        ProgressResponse: The updated record with new values reflected.

    Raises:
        HTTPException 400: If no record with that id exists.
    """
    return progress_service.update_progress(db, progress_id, data)


@router.delete(
    "/{progress_id}",
    response_model=bool,
    summary="Delete a progress record",
    description="Permanently removes a progress record from the database. Returns True on success.",
)
def delete_progress(progress_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a progress record by primary key.

    Args:
        progress_id: Primary key of the record to delete.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the record was found and deleted.

    Raises:
        HTTPException 400: If no record with that id exists.
    """
    progress_service.delete_progress(db, progress_id)
    return True
