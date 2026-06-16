"""
auth.py — Authentication Router

Handles login for Staff (managers and trainers).
On successful login, returns a signed JWT access token.

Uses OAuth2PasswordRequestForm — the industry-standard OAuth2 form format.
The client sends username (email) and password as form fields.
Staff email is looked up globally across all gyms.

The token payload contains:
    sub  — staff id (as string)
    role — staff role (manager or trainer)
    gym  — gym id the staff belongs to

Route summary:
    POST /auth/login → verify credentials, return JWT token

Error handling:
    Email not found   → 401 Unauthorized
    Wrong password    → 401 Unauthorized
    No password set   → 401 Unauthorized
"""
from fastapi.security import OAuth2PasswordRequestForm
from typing import cast
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database.session import get_db
from app.repository import staff_repository
from app.core.security import verify_password, create_access_token
from app.core.rate_limit import limiter
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    """JWT token returned on successful login."""
    access_token: str
    token_type: str = "bearer"


# --- Endpoints ---

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Staff login",
    description=(
        "Authenticates a staff member using email (sent as username) and password. "
        "Uses OAuth2 password flow — compatible with Swagger Authorize and standard OAuth2 clients. "
        "Returns a signed JWT access token valid for 30 minutes."
    ),
)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a staff member and return a JWT access token.

    Args:
        form_data: OAuth2PasswordRequestForm — username field used as email, plus password.
        db: Database session injected by FastAPI.

    Returns:
        TokenResponse: JWT access token and token type ("bearer").

    Raises:
        HTTPException 401: If no staff with that email exists, if no password is set,
                           or if the password does not match the stored hash.
    """
    # Step 1: Look up staff by email within the gym
    staff = staff_repository.get_by_email_global(db, form_data.username)

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Step 2: Verify the password against the stored hash
    hashed = cast(str | None, staff.hashed_password)
    if not hashed or not verify_password(form_data.password, hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Step 3: Build token payload and return signed JWT
    token = create_access_token({
        "sub": str(staff.id),
        "role": staff.role.value,
        "gym": staff.gym_id,
    })
    logger.info("Staff login successful: %s (role=%s)",
                form_data.username, staff.role.value)

    return TokenResponse(access_token=token)
