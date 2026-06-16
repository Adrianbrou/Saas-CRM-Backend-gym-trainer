"""
gyms.py — Gyms API Router

Handles all HTTP endpoints for Gym resources.
Gyms are the top-level tenant in the system — all other resources
(staff, members, sessions) belong to a gym via gym_id.

Route summary:
    POST   /gyms/           → register a new gym
    GET    /gyms/           → list all gyms in the system
    GET    /gyms/{gym_id}   → retrieve one gym by id
    PATCH  /gyms/{gym_id}   → partially update a gym
    DELETE /gyms/{gym_id}   → remove a gym and all its dependents

Error handling:
    ValueError from service layer → 400 Bad Request (duplicate)
    ValueError from service layer → 404 Not Found (gym does not exist)
"""

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.gym import GymCreate, GymResponse, GymUpdate
from app.services import gym_service
from app.core.dependency import get_current_user, require_manager


router = APIRouter(prefix="/gyms", tags=["gyms"])


@router.post(
    "/",
    response_model=GymResponse,
    summary="Register a new gym",
    description=(
        "Creates a new gym (tenant). "
        "The combination of name + location must be unique — "
        "two gyms with the same name can exist as long as they are in different locations."
    ),
    status_code=201,
)
def create_gym(data: GymCreate, db: Session = Depends(get_db)):
    """Register a new gym.

    Args:
        data: GymCreate schema — name, location.
        db: Database session injected by FastAPI.

    Returns:
        GymResponse: The newly created gym including id and timestamps.

    Raises:
        HTTPException 400: If a gym with the same name and location already exists.
    """
    return gym_service.register_gym(db, data)


@router.get(
    "/",
    response_model=list[GymResponse],
    summary="List all gyms",
    description="Returns every gym registered in the system. May return an empty list.",
    status_code=200,
)
def get_all_gym(_=Depends(get_current_user), db: Session = Depends(get_db), skip: int = 0, limit: int = 20):
    """Retrieve all gyms in the system.

    Args:
        db: Database session injected by FastAPI.
        skip: Number of records to skip. Defaults to 0.
        limit: Maximum number of records to return. Defaults to 20.

    Returns:
        list[GymResponse]: All gyms (may be empty).
    """
    return gym_service.get_all(db, skip=skip, limit=limit)


@router.get(
    "/{gym_id}",
    response_model=GymResponse,
    summary="Get a gym by id",
    description="Returns a single gym identified by its primary key.",
)
def get_gym_id(gym_id: int, _=Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve one gym by primary key.

    Args:
        gym_id: Primary key of the gym to retrieve.
        db: Database session injected by FastAPI.

    Returns:
        GymResponse: The matching gym.

    Raises:
        HTTPException 404: If no gym with that id exists.
    """
    return gym_service.get_gym(db, gym_id)


@router.patch(
    "/{gym_id}",
    response_model=GymResponse,
    summary="Update a gym",
    description=(
        "Partially updates a gym. Only send the fields you want to change. "
        "If updating name or location, the new name + location combination must remain unique."
    ),
)
def update_gym(data: GymUpdate, gym_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Partially update a gym's fields.

    Args:
        data: GymUpdate schema — all fields optional (name, location).
        gym_id: Primary key of the gym to update.
        db: Database session injected by FastAPI.

    Returns:
        GymResponse: The updated gym with new values reflected.

    Raises:
        HTTPException 404: If no gym with that id exists.
    """
    return gym_service.update_gym(db, gym_id, data)


@router.delete(
    "/{gym_id}",
    response_model=bool,
    summary="Delete a gym",
    description=(
        "Permanently removes a gym and all its dependents (staff, members, sessions) "
        "from the database via cascade delete. Returns True on success."
    ),
)
def delete(gym_id: int, _=Depends(require_manager), db: Session = Depends(get_db)):
    """Delete a gym by primary key.

    Args:
        gym_id: Primary key of the gym to delete.
        db: Database session injected by FastAPI.

    Returns:
        bool: True if the gym was found and deleted.

    Raises:
        HTTPException 404: If no gym with that id exists.
    """
    return gym_service.delete_gym(db, gym_id)
