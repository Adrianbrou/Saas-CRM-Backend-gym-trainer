import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.gyms import router as gym_router
from app.api.staff import router as staff_router
from app.api.members import router as member_router
from app.api.progress import router as progress_router
from app.api.workout_sessions import router as workout_sessions_router
from app.api.workouts import router as workout_router
from app.api.auth import router as auth_router
from app.core.logging_config import setup_logging
from app.core.exceptions import AppError, NotFoundError, DuplicateError, BusinessRuleError
from app.core.rate_limit import limiter
from app.database.session import get_db
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded


setup_logging()
logger = logging.getLogger(__name__)


app = FastAPI()

# Rate limiting: attach the shared limiter to the app and register the 429 handler.
# Routes opt in with @limiter.limit(...) - see app/api/auth.py for the login limit.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# --- Domain exception handlers --------------------------------------------------
# The service layer raises typed domain errors; this is the ONE place that maps each
# to an HTTP status. Routers stay clean and the mapping is consistent across the API.

@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DuplicateError)
def handle_duplicate(request: Request, exc: DuplicateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(BusinessRuleError)
def handle_business_rule(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # Fallback for any AppError not matched by a more specific handler above.
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Liveness probe that actually verifies database connectivity.

    Returns 200 either way (the endpoint itself is up) but reports whether the DB
    round-trip succeeded, so an uptime monitor can distinguish "app up, DB down".
    """
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("health check: database ping failed", exc_info=True)
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "version": "1.0.0",
    }


app.include_router(auth_router)
app.include_router(gym_router)
app.include_router(staff_router)
app.include_router(member_router)
app.include_router(progress_router)
app.include_router(workout_sessions_router)
app.include_router(workout_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)  # uvicorn app.main:app --reload
