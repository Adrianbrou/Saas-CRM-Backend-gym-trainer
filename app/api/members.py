"""
members.py — Members API Router

Handles all HTTP endpoints for Member resources.
Members are tenant-scoped: every member belongs to a gym via gym_id.
Email must be unique per gym — two gyms can share an email,
but one gym cannot have two members with the same email.

Route summary:
    POST   /members/                → register a new member in a gym
    GET    /members/gyms/{gym_id}   → list all members belonging to a gym
    GET    /members/{member_id}     → retrieve one member by id
    PATCH  /members/{member_id}     → partially update a member
    DELETE /members/{member_id}     → remove a member

Error handling:
    ValueError from service layer → 400 Bad Request (duplicate or not found)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import member_service
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from app.core.dependency import get_current_user, require_manager
from app.models.staff import Staff
from fastapi import BackgroundTasks
from app.core.email import send_welcome_email
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/members", tags=["members"])


@router.post(
    "/",
    response_model=MemberResponse,
    summary="Register a new member",
    description=(
        "Creates a new member linked to the specified gym. "
        "Email must be unique within the gym — two gyms can share an email, "
        "but one gym cannot have two members with the same email."
    ), status_code=201,
)
def create_member(background_tasks: BackgroundTasks, data: MemberCreate, current_user: Staff = Depends(require_manager), db: Session = Depends(get_db)):
    """Register a new gym member.

    Args:
        background_tasks: FastAPI BackgroundTasks — used to dispatch the welcome email after save.
        data: MemberCreate schema — gym_id, name, email, phone.
        db: Database session injected by FastAPI.

    Returns:
        MemberResponse: The newly created member including id and timestamps.

    Raises:
        HTTPException 400: If a member with that email already exists in the gym.
    """
    # Tenant isolation: a manager may only create members inside their OWN gym.
    # gym_id comes from the request body, so we check it against the gym on the JWT-
    # authenticated staff. Without this, an authenticated manager could create members
    # in any gym (horizontal privilege escalation / IDOR).
    if data.gym_id != current_user.gym_id:
        raise HTTPException(status_code=403, detail="You can only manage your own gym")

    member = member_service.register_member(db, data)
    logger.info("Member registered: %s (gym_id=%s)", data.email, data.gym_id)
    background_tasks.add_task(send_welcome_email, data.email, data.name)
    return member


@router.get(
    "/gyms/{gym_id}",
    response_model=list[MemberResponse],
    summary="List all members in a gym",
    description="Returns every member belonging to the given gym. May return an empty list.",
)
def get_all(gym_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all members for a specific gym.

    Args:
        gym_id: Primary key of the gym to query.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[MemberResponse]: All members linked to that gym (may be empty).
    """
    return member_service.get_all(db, gym_id, skip=skip, limit=limit)


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get a member by id",
    description="Returns a single member identified by their primary key.",
)
def get_member(member_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve one member by primary key.

    Args:
        member_id: Primary key of the member.
        db: Database session injected by FastAPI.

    Returns:
        MemberResponse: The matching member.

    Raises:
        HTTPException 400: If no member with that id exists.
    """
    return member_service.get_member(db, member_id)


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update a member",
    description=(
        "Partially updates a member. Only send the fields you want to change. "
        "gym_id cannot be changed — members cannot be reassigned to a different gym."
    ),
)
def update_member(member_id: int, data: MemberUpdate, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Partially update a member's fields.

    Args:
        member_id: Primary key of the member to update.
        data: MemberUpdate schema — all fields optional (name, email, phone).
        db: Database session injected by FastAPI.

    Returns:
        MemberResponse: The updated member with new values reflected.

    Raises:
        HTTPException 400: If no member with that id exists.
    """
    return member_service.update_member(db, member_id, data)


@router.delete(
    "/{member_id}",
    response_model=bool,
    summary="Delete a member",
    description="Permanently removes a member from the database. Returns True on success.",
)
def delete_member(member_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Delete a member by primary key.

    Args:
        member_id: Primary key of the member to delete.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the member was found and deleted.

    Raises:
        HTTPException 400: If no member with that id exists.
    """
    return member_service.delete_member(db, member_id)
