from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.main import app
from app.database.session import get_db as real_get_db
from fastapi.testclient import TestClient
import pytest

# Use SQLite for tests — fast, no install needed, wiped after each test
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Test engine — points to SQLite instead of PostgreSQL
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite only
)

# Test session factory — same as production SessionLocal but uses test engine
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Test version of get_db — opens a SQLite session instead of PostgreSQL."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# STUNT DOUBLE — swap real get_db for test get_db in ALL endpoints
# Every endpoint that uses Depends(get_db) will now get the SQLite session
app.dependency_overrides[real_get_db] = get_db

# Disable rate limiting during tests: many tests log in, which would otherwise trip the
# per-IP login limit. test_rate_limit.py re-enables it explicitly to prove the 429.
from app.core.rate_limit import limiter as _limiter
_limiter.enabled = False


@pytest.fixture
def db():
    """Unit test fixture — injects a clean SQLite session, wipes DB after test."""
    Base.metadata.create_all(bind=engine)   # create all tables
    db = TestingSessionLocal()
    try:
        yield db                             # test runs here
    finally:
        db.close()
        # wipe all tables — fresh start next test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Integration test fixture — spins up a fake HTTP server using the test DB."""
    Base.metadata.create_all(bind=engine)   # create all tables
    with TestClient(app) as c:
        yield c                              # test makes HTTP requests here
    Base.metadata.drop_all(bind=engine)     # wipe all tables after test


@pytest.fixture
def auth_client(client):
    from app.models.staff import Staff, RoleEnum
    from app.core.security import hash_password

    # create gym via API (open endpoint)
    gym_response = client.post(
        "/gyms/", json={"name": "Test Gym", "location": "Test City"})
    gym_id = gym_response.json()["id"]

    # create staff directly in DB (bypasses auth)
    db = TestingSessionLocal()
    staff = Staff(
        name="Manager",
        email="manager@test.com",
        phone="123456789",
        role=RoleEnum.manager,
        gym_id=gym_id,
        hashed_password=hash_password("testpass123")
    )
    db.add(staff)
    db.commit()
    db.close()

    # login via API
    response = client.post("/auth/login", data={
        "username": "manager@test.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
