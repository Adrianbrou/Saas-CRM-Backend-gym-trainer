"""
workout_session_service.py — Business Logic for WorkoutSession

This service manages three operations:
  1. create_session              — create a new workout session for a gym
  2. add_member_to_session       — register a member as attending a session
  3. remove_member_from_session  — remove a member from a session

KEY RULE: The trainer assigned to a session must belong to the same gym.
KEY RULE: The member added to a session must exist before adding attendance.

FLOW REMINDER:
  API → Service (business rules) → Repository (DB operations)
  The service never touches the DB directly.
"""

from app.models.workout_session import WorkoutSession, Attendance
from app.repository import workout_session_repository, staff_repository, member_repository
from app.schemas.workout_session import WorkoutSessionCreate, AttendanceCreate
from app.core.exceptions import NotFoundError, BusinessRuleError
from sqlalchemy.orm import Session


def create_session(db: Session, data: WorkoutSessionCreate) -> WorkoutSession:
    """Create a new workout session after validating the trainer belongs to the gym.

    Business rules enforced:
      - Trainer (staff) must exist
      - Trainer must belong to the same gym as the session

    Args:
        db: SQLAlchemy session injected by the caller.
        data: Validated WorkoutSessionCreate schema (gym_id, staff_id, scheduled_at).

    Raises:
        ValueError: If trainer not found or does not belong to this gym.

    Returns:
        The newly created WorkoutSession with database-generated id.
    """
    # Step 1: Check trainer exists
    trainer = staff_repository.get_by_id(db, data.staff_id)
    if not trainer:
        raise BusinessRuleError("Trainer not found")

    # Step 2: Check trainer belongs to this gym
    # A trainer from Gym A cannot lead a session at Gym B
    if trainer.gym_id != data.gym_id:
        raise BusinessRuleError("Trainer does not belong to this gym")

    # Step 3: Build WorkoutSession object and save — same pattern as register_gym
    workout_session = WorkoutSession(**data.model_dump())
    return workout_session_repository.create(db, workout_session)


def get_all(db: Session, gym_id: int, skip: int = 0, limit: int = 20) -> list[WorkoutSession]:
    """this function is the retrieve the all Workouts information  from the db
    Args:
        db (Session): Session to the database
        gym_id (int): The id of the gym whose sessions to retrieve.
        skip (int): Number of records to skip. Defaults to 0.
        limit (int): Maximum number of records to return. Defaults to 20.

    Returns:
        all Workouts found as list  in the gym
    """

    return workout_session_repository.get_all(db, gym_id, skip=skip, limit=limit)


def add_member_to_session(db: Session, data: AttendanceCreate) -> Attendance:
    """Add a member to a workout session by creating an Attendance record.

    Attendance is a junction table — it simply links a member to a session.
    Business rules enforced:
      - Session must exist
      - Member must exist

    Args:
        db: SQLAlchemy session injected by the caller.
        data: Validated AttendanceCreate schema (workout_session_id, member_id).

    Raises:
        ValueError: If session or member not found.

    Returns:
        The newly created Attendance record linking member to session.
    """
    # Step 1: Check the session exists
    session = workout_session_repository.get_by_id(db, data.workout_session_id)
    if not session:
        raise NotFoundError("Session not found")

    # Step 2: Check the member exists
    member = member_repository.get_by_id(db, data.member_id)
    if not member:
        raise NotFoundError("Member not found")

    # Step 3: Build Attendance object and save it
    attendance = Attendance(**data.model_dump())
    return workout_session_repository.create(db, attendance)


def remove_member_from_session(db: Session, session_id: int, member_id: int) -> bool:
    """Remove a member from a workout session by deleting their Attendance record.

    Args:
        db: SQLAlchemy session injected by the caller.
        session_id: Primary key of the WorkoutSession.
        member_id: Primary key of the Member to remove.

    Raises:
        ValueError: If session not found.

    Returns:
        True if attendance record deleted, False if member was not in the session.
    """
    # Step 1: Check the session exists
    session = workout_session_repository.get_by_id(db, session_id)
    if not session:
        raise NotFoundError("Session not found")

    # Step 2: Delegate attendance removal to the repository
    return workout_session_repository.remove_attendance(db, session_id, member_id)
