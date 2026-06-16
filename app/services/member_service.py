"""
member_service.py — Business Logic for Member

Members are tenant-scoped: each member belongs to a gym via gym_id.
Email must be unique per gym — two members at different gyms can share an email,
but not two members at the same gym.
"""

from app.models.member import Member
from app.repository import member_repository
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from sqlalchemy.orm import Session
from app.core import cache
from app.core.exceptions import NotFoundError, DuplicateError


def register_member(db: Session, data: MemberCreate) -> Member:
    """Register a new member after verifying the email is not already taken in this gym.

    Args:
        db (Session): Session to the database.
        data (MemberCreate): Validated schema containing name, email, phone, gym_id.

    Raises:
        ValueError: If a member with the same email already exists in this gym.

    Returns:
        Member: The newly created member with database-generated id and timestamps.
    """
    existing = member_repository.get_by_email(db, data.email, data.gym_id)
    if existing:
        raise DuplicateError("Member already exists")
    member = Member(**data.model_dump())
    return member_repository.create(db, member)


def update_member(db: Session, member_id: int, data: MemberUpdate) -> Member:
    """Update an existing member's fields after verifying the member exists.

    Args:
        db (Session): Session to the database.
        member_id (int): Primary key of the member to update.
        data (MemberUpdate): Validated schema — all fields optional.

    Raises:
        ValueError: If no member with that id exists.

    Returns:
        Member: The updated member with new values reflected.
    """
    existing = member_repository.get_by_id(db, member_id)
    if not existing:
        raise NotFoundError("Member not found")
    updates = data.model_dump(exclude_unset=True)
    result = member_repository.update(db, member_id, updates)
    cache.redis_client.delete(f"member:{member_id}")
    return result


def get_all(db: Session, gym_id: int, skip: int = 0, limit: int = 20) -> list[Member]:
    """this function is the retrieve the all member information  from the db
    Args:
        db (Session): Session to the database
        gym_id (int): The id of the gym whose members to retrieve.
        skip (int): Number of records to skip. Defaults to 0.
        limit (int): Maximum number of records to return. Defaults to 20.

    Returns:
        all member found as list  in the gym
    """

    return member_repository.get_all(db, gym_id, skip=skip, limit=limit)


def get_member(db: Session, member_id: int) -> MemberResponse:
    """Retrieve a member by id after verifying the member exists.

    Args:
        db (Session): Session to the database.
        member_id (int): Primary key of the member to retrieve.

    Raises:
        ValueError: If no member with that id exists.

    Returns:
        Member: The matching member object.
    """
    # Return a validated MemberResponse on BOTH the cache-hit and cache-miss paths,
    # so this function has one return type regardless of whether Redis was warm.
    cached = cache.redis_client.get(f"member:{member_id}")
    if cached and isinstance(cached, str):
        return MemberResponse.model_validate_json(cached)

    existing = member_repository.get_by_id(db, member_id)
    if not existing:
        raise NotFoundError("Member not found")

    response = MemberResponse.model_validate(existing)
    cache.redis_client.set(f"member:{member_id}", response.model_dump_json(), ex=300)
    return response


def delete_member(db: Session, member_id: int) -> bool:
    """Delete a member after verifying the member exists.

    Args:
        db (Session): Session to the database.
        member_id (int): Primary key of the member to delete.

    Raises:
        ValueError: If no member with that id exists.

    Returns:
        bool: True if the member was found and deleted.
    """
    existing = member_repository.get_by_id(db, member_id)
    if not existing:
        raise NotFoundError("Member not found")
    member_repository.delete(db, member_id)
    cache.redis_client.delete(f"member:{member_id}")
    return True
