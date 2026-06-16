"""
gym_service.py — Business Logic for Gym

The service layer sits between the API and the repository.
It enforces business rules before delegating to the repository.

FLOW:
  API receives request
    → calls service function
      → service checks business rules
        → service calls repository
          → repository talks to DB
            → result bubbles back up
"""

from app.repository import gym_repository
from app.models.gym import Gym
from app.schemas.gym import GymCreate, GymUpdate, GymResponse
from sqlalchemy.orm import Session
from app.core import cache
from app.core.exceptions import NotFoundError, DuplicateError


def register_gym(db: Session, data: GymCreate) -> Gym:
    """Create a new gym after verifying the name is not already taken.

    WHY THIS EXISTS:
        The repository's create() would blindly save any Gym object you give it.
        It has no idea if a gym with that name already exists.
        The service enforces the business rule: gym names must be unique.

    HOW IT WORKS:
        1. Calls gym_repository.get_by_name_location() to check if a gym with
           the same name AND location already exists (duplicate check).
        2. If found → raises ValueError. The API layer will catch this
           and return a 400 Bad Request to the client.
        3. If not found → builds a Gym SQLAlchemy object from the schema data
           using model_dump(), which converts the Pydantic object to a plain dict.
           The ** unpacks that dict into keyword arguments: Gym(name=..., location=...).
        4. Passes the new Gym object to gym_repository.create() to save it.

    Args:
        db: SQLAlchemy session injected by the caller (API route).
        data: Validated GymCreate schema containing name and location.

    Returns:
        The newly created Gym with its database-generated id and timestamps.

    Raises:
        ValueError: If a gym with the same name already exists.
    """
    # Step 1: Business rule — no duplicate gym names
    existing = gym_repository.get_by_name_location(
        db, data.name, data.location)
    if existing:
        raise DuplicateError("Gym already exists")

    # Step 2: Build the SQLAlchemy model object from the Pydantic schema
    # model_dump() converts the Pydantic schema to a dict, and ** unpacks it into keyword arguments.
    gym = Gym(**data.model_dump())

    # Step 3: Delegate saving to the repository
    return gym_repository.create(db, gym)


def update_gym(db: Session, gym_id: int, data: GymUpdate) -> Gym:
    """Update an existing gym's fields after verifying it exists.

    WHY THIS EXISTS:
        The repository's update() would silently return None if the gym
        doesn't exist. The service raises an explicit error instead,
        so the API can return a proper 404 Not Found to the client.

    HOW IT WORKS:
        1. Calls gym_repository.get_by_id() to verify the gym exists.
        2. If not found → raises ValueError.
        3. If found → calls model_dump(exclude_unset=True) on the schema.
           exclude_unset=True is critical: it only includes fields the client
           actually sent. If the client only sent {"location": "Toronto"},
           the dict will be {"location": "Toronto"} — NOT {"name": None, "location": "Toronto"}.
           Without this, you'd accidentally overwrite name with None.
        4. Passes gym_id and the updates dict to gym_repository.update().

    Args:
        db: SQLAlchemy session injected by the caller (API route).
        gym_id: Primary key of the gym to update.
        data: Validated GymUpdate schema — all fields optional.

    Returns:
        The updated Gym object with new values reflected.

    Raises:
        ValueError: If no gym with that id exists.
    """
    # Step 1: Business rule — gym must exist before updating
    existing = gym_repository.get_by_id(db, gym_id)
    if not existing:
        raise NotFoundError("Gym not found")

    # Step 2: Convert only the fields the client sent (skip unset None fields)
    # exclude_unset=True means "only include fields the client actually sent, skip the None ones".
    updates = data.model_dump(exclude_unset=True)

    # Step 3: Delegate the actual DB update to the repository
    result = gym_repository.update(db, gym_id, updates)
    cache.redis_client.delete(f"gym:{gym_id}")

    return result


def get_gym(db: Session, gym_id: int) -> GymResponse:
    """this function is the retrieve the gym information (id) from the db , the service layer check if this gym exist
        if yes authorize the retrieval, if not raise a value Error
    Args:
        db (Session): Session to the database 
        gym_id (int): the id to check for get the info

    Raises:
        ValueError: check if gym exist or not

    Returns:
        Gym: if existing return the gym info through it's id
    """

    # Return a validated GymResponse on both the cache-hit and cache-miss paths.
    cached = cache.redis_client.get(f"gym:{gym_id}")
    if cached and isinstance(cached, str):
        return GymResponse.model_validate_json(cached)

    existing = gym_repository.get_by_id(db, gym_id)
    if not existing:
        raise NotFoundError("Gym not found")

    response = GymResponse.model_validate(existing)
    cache.redis_client.set(f"gym:{gym_id}", response.model_dump_json(), ex=300)
    return response


def get_all(db: Session, skip: int = 0, limit: int = 20) -> list[Gym]:
    """this function is the retrieve the all gym information  from the db
    Args:
        db (Session): Session to the database
        skip (int): Number of records to skip. Defaults to 0.
        limit (int): Maximum number of records to return. Defaults to 20.

    Returns:
        all gym found as list
    """

    return gym_repository.get_all(db, skip=skip, limit=limit)


def delete_gym(db: Session, gym_id: int) -> bool:
    """Delete a gym after verifying it exists.

    Args:
        db (Session): Session to the database.
        gym_id (int): The id of the gym to delete.

    Raises:
        ValueError: If no gym with that id exists.

    Returns:
        bool: True if the gym was found and deleted.
    """
    existing = gym_repository.get_by_id(db, gym_id)
    if not existing:
        raise NotFoundError("Gym not found")
    gym_repository.delete(db, gym_id)
    cache.redis_client.delete(f"gym:{gym_id}")

    return True
