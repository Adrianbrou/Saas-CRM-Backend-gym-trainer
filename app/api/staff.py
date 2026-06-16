"""
staff.py — Staff API Router

Handles all HTTP endpoints for Staff resources.
Staff are tenant-scoped: every staff member belongs to a gym via gym_id.
Roles are restricted to RoleEnum values: 'manager' or 'trainer'.

Route summary:
    POST   /staff/              → register a new staff member in a gym
    GET    /staff/gym/{gym_id}  → list all staff belonging to a gym
    GET    /staff/{staff_id}    → retrieve one staff member by id
    PATCH  /staff/{staff_id}    → partially update a staff member
    DELETE /staff/{staff_id}    → remove a staff member

Error handling:
    ValueError from service layer → 400 Bad Request (duplicate, not found, etc.)
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services import staff_service
from app.schemas.staff import StaffCreate, StaffResponse, StaffUpdate
from app.core.dependency import get_current_user, require_manager
from app.models.staff import Staff


router = APIRouter(prefix="/staff", tags=["staff"])


@router.post(
    "/",
    response_model=StaffResponse,
    summary="Register a new staff member",
    description=(
        "Creates a new staff member linked to the specified gym. "
        "Role Can be only 'manager' or 'trainer'"
        "Email must be unique within the gym — two gyms can share an email, "
        "but one gym cannot have two staff members with the same email."
    ), status_code=201,
)
def create_staff(data: StaffCreate, current_user: Staff = Depends(require_manager), db: Session = Depends(get_db)):
    """Register a new staff member.

    Args:
        data: StaffCreate schema — role, name, email, phone, gym_id.
        db: Database session injected by FastAPI.

    Returns:
        StaffResponse: The newly created staff member including id and timestamps.

    Raises:
        HTTPException 400: If a staff member with that email already exists in the gym.
    """
    if data.gym_id != current_user.gym_id:
        raise HTTPException(status_code=403, detail="You can only manage your own gym")
    return staff_service.register_staff(db, data)


@router.get(
    "/gym/{gym_id}",
    response_model=list[StaffResponse],
    summary="List all staff in a gym",
    description="Returns every staff member (managers and trainers) belonging to the given gym.",
)
def get_all_staff(gym_id: int, _=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all staff members for a specific gym.

    Args:
        gym_id: Primary key of the gym to query.
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[StaffResponse]: All staff members linked to that gym (may be empty).
    """
    return staff_service.get_all(db, gym_id, skip=skip, limit=limit)


@router.get(
    "/{staff_id}",
    response_model=StaffResponse,
    summary="Get a staff member by id",
    description="Returns a single staff member identified by their primary key.",
)
def get_staff(staff_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve one staff member by primary key.

    Args:
        staff_id: Primary key of the staff member.
        db: Database session injected by FastAPI.

    Returns:
        StaffResponse: The matching staff member.

    Raises:
        HTTPException 400: If no staff member with that id exists.
    """
    return staff_service.get_staff(db, staff_id)


@router.patch(
    "/{staff_id}",
    response_model=StaffResponse,
    summary="Update a staff member",
    description=(
        "Partially updates a staff member. Only send the fields you want to change. "
        "gym_id cannot be changed — staff cannot be reassigned to a different gym."
    ),
)
def update_staff(staff_id: int, data: StaffUpdate, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Partially update a staff member's fields.

    Args:
        staff_id: Primary key of the staff member to update.
        data: StaffUpdate schema — all fields optional (role, name, email, phone).
        db: Database session injected by FastAPI.

    Returns:
        StaffResponse: The updated staff member with new values reflected.

    Raises:
        HTTPException 400: If no staff member with that id exists.
    """
    return staff_service.update_staff(db, staff_id, data)


@router.delete(
    "/{staff_id}",
    response_model=bool,
    summary="Delete a staff member",
    description="Permanently removes a staff member from the database. Returns True on success.",
)
def delete_staff(staff_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Delete a staff member by primary key.

    Args:
        staff_id: Primary key of the staff member to delete.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the staff member was found and deleted.

    Raises:
        HTTPException 400: If no staff member with that id exists.
    """
    return staff_service.delete_staff(db, staff_id)
