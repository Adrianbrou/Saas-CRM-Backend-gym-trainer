"""
workout_sessions.py — Workout Sessions API Router

Handles all HTTP endpoints for WorkoutSession and Attendance resources.
Sessions are gym-scoped: every session belongs to a gym via gym_id.
A session must be assigned to a trainer (Staff) who belongs to the same gym.
Attendance links members to sessions via a junction table.

Route summary:
    POST   /workout-sessions/                                    → create a new session
    GET    /workout-sessions/gyms/{gym_id}                       → list all sessions for a gym
    POST   /workout-sessions/{session_id}/members                → add a member to a session
    DELETE /workout-sessions/{session_id}/members/{member_id}    → remove a member from a session

Error handling:
    ValueError from service layer → 400 Bad Request (not found or gym mismatch)
"""
from fastapi import BackgroundTasks
from app.core.email import send_session_notification
from app.repository import member_repository, staff_repository, gym_repository, workout_session_repository


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import workout_session_service
from app.schemas.workout_session import (
    WorkoutSessionCreate,
    WorkoutSessionResponse,
    AttendanceCreate,
    AttendanceResponse,
)
from app.core.dependency import get_current_user, require_manager
from app.models.staff import Staff


router = APIRouter(prefix="/workout-sessions", tags=["workout-sessions"])


@router.post(
    "/",
    response_model=WorkoutSessionResponse,
    summary="Create a new workout session",
    description=(
        "Creates a new workout session for a gym. "
        "The assigned trainer (staff_id) must belong to the same gym as the session. "
        "A trainer from another gym cannot lead a session."
    ), status_code=201,
)
def create_session(data: WorkoutSessionCreate, current_user: Staff = Depends(require_manager), db: Session = Depends(get_db)):
    """Create a new workout session.

    Args:
        data: WorkoutSessionCreate schema — gym_id, staff_id, scheduled_at.
        db: Database session injected by FastAPI.

    Returns:
        WorkoutSessionResponse: The newly created session including id and timestamps.

    Raises:
        HTTPException 400: If the trainer does not exist or does not belong to this gym.
    """
    if data.gym_id != current_user.gym_id:
        raise HTTPException(status_code=403, detail="You can only manage your own gym")
    return workout_session_service.create_session(db, data)


@router.get(
    "/gyms/{gym_id}",
    response_model=list[WorkoutSessionResponse],
    summary="List all sessions for a gym",
    description="Returns every workout session scheduled for the given gym. May return an empty list.",
)
def get_all(gym_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all workout sessions for a specific gym.

    Args:
        gym_id: Primary key of the gym to query.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[WorkoutSessionResponse]: All sessions for that gym (may be empty).
    """
    return workout_session_service.get_all(db, gym_id, skip=skip, limit=limit)


@router.post(
    "/{session_id}/members",
    response_model=AttendanceResponse,
    summary="Add a member to a session",
    description=(
        "Registers a member as attending a workout session. "
        "Both the session and the member must already exist."
    ), status_code=201,
)
def add_member(background_tasks: BackgroundTasks, session_id: int, data: AttendanceCreate, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Add a member to a workout session.

    Args:
        session_id: Primary key of the session (used for route clarity — also in data).
        data: AttendanceCreate schema — workout_session_id, member_id.
        db: Database session injected by FastAPI.

    Returns:
        AttendanceResponse: The created attendance record linking member to session.

    Raises:
        HTTPException 400: If the session or member does not exist.
    """
    if data.workout_session_id != session_id:
        raise HTTPException(
            status_code=400, detail="session_id in URL does not match body")
    attendance = workout_session_service.add_member_to_session(db, data)
    member = member_repository.get_by_id(db, data.member_id)
    session = workout_session_repository.get_by_id(db, data.workout_session_id)
    trainer = staff_repository.get_by_id(db, session.staff_id)  # type: ignore
    gym = gym_repository.get_by_id(db, session.gym_id)  # type: ignore
    background_tasks.add_task(send_session_notification, member.email, trainer.name,  # type: ignore
                              member.name, gym.name, session.scheduled_at)  # type: ignore
    return attendance


@router.delete(
    "/{session_id}/members/{member_id}",
    response_model=bool,
    summary="Remove a member from a session",
    description=(
        "Removes a member's attendance record from a workout session. "
        "Returns True if removed, False if the member was not in the session."
    ),
)
def remove_member(session_id: int, member_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Remove a member from a workout session.

    Args:
        session_id: Primary key of the workout session.
        member_id: Primary key of the member to remove.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the attendance record was deleted, False if not found.

    Raises:
        HTTPException 400: If the session does not exist.
    """
    return workout_session_service.remove_member_from_session(db, session_id, member_id)
