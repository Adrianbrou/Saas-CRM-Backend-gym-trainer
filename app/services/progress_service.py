from sqlalchemy.orm import Session
from app.repository import progress_repository
from app.models.progress import Progress
from app.schemas.progress import ProgressCreate, ProgressUpdate, ProgressResponse
from app.core import cache
from app.core.exceptions import NotFoundError


def log_progress(db: Session, data: ProgressCreate) -> Progress:
    """Log a new progress record for a member.

    Args:
        db: SQLAlchemy session injected by the caller.
        data: Validated ProgressCreate schema from the API layer.

    Returns:
        The newly created Progress record.
    """
    progress = Progress(**data.model_dump())
    return progress_repository.create(db, progress)


def get_progress(db: Session, progress_id: int) -> ProgressResponse:
    """Fetch a single progress record by ID.

    Args:
        db: SQLAlchemy session injected by the caller.
        progress_id: Primary key of the record to retrieve.

    Returns:
        The matching Progress record.

    Raises:
        ValueError: If no record exists with the given ID.
    """
    # Return a validated ProgressResponse on both the cache-hit and cache-miss paths.
    cached = cache.redis_client.get(f"progress:{progress_id}")
    if cached and isinstance(cached, str):
        return ProgressResponse.model_validate_json(cached)

    progress = progress_repository.get_by_id(db, progress_id)
    if not progress:
        raise NotFoundError(f"Progress record {progress_id} not found.")
    response = ProgressResponse.model_validate(progress)
    cache.redis_client.set(f"progress:{progress_id}", response.model_dump_json(), ex=300)
    return response


def get_all(db: Session, skip: int = 0, limit: int = 20) -> list[Progress]:
    """this function is the retrieve the all Progress information  from the db
    Args:
        db (Session): Session to the database
        skip (int): Number of records to skip. Defaults to 0.
        limit (int): Maximum number of records to return. Defaults to 20.

    Returns:
        all Progress found as list
    """

    return progress_repository.get_all(db, skip=skip, limit=limit)


def update_progress(db: Session, progress_id: int, data: ProgressUpdate) -> Progress:
    """Partially update an existing progress record.

    Args:
        db: SQLAlchemy session injected by the caller.
        progress_id: Primary key of the record to update.
        data: Validated ProgressUpdate schema (only sent fields applied).

    Returns:
        The updated Progress record.

    Raises:
        ValueError: If no record exists with the given ID.
    """
    progress = progress_repository.get_by_id(db, progress_id)
    if not progress:
        raise NotFoundError(f"Progress record {progress_id} not found.")
    updates = data.model_dump(exclude_unset=True)
    result = progress_repository.update(db, progress_id, updates)
    cache.redis_client.delete(f"progress:{progress_id}")
    return result


def delete_progress(db: Session, progress_id: int) -> None:
    """Delete a progress record by ID.

    Args:
        db: SQLAlchemy session injected by the caller.
        progress_id: Primary key of the record to delete.

    Raises:
        ValueError: If no record exists with the given ID.
    """
    deleted = progress_repository.delete(db, progress_id)
    if not deleted:
        raise NotFoundError(f"Progress record {progress_id} not found.")
    cache.redis_client.delete(f"progress:{progress_id}")


def get_progress_by_member(db: Session, member_id: int, skip: int = 0, limit: int = 20) -> list[Progress]:
    """Fetch all progress records for a member."""
    return progress_repository.get_by_member(db, member_id, skip=skip, limit=limit)


def get_progress_by_workout(db: Session, workout_id: int, skip: int = 0, limit: int = 20) -> list[Progress]:
    """Fetch all progress records for a specific workout."""
    return progress_repository.get_by_workout(db, workout_id, skip=skip, limit=limit)


def get_progress_by_session(db: Session, session_id: int, skip: int = 0, limit: int = 20) -> list[Progress]:
    """Fetch all progress records logged in a specific workout session."""
    return progress_repository.get_by_session_id(db, session_id, skip=skip, limit=limit)
