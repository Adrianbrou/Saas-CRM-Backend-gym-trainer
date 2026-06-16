"""
seed_demo_user.py - create a known manager you can log in with (LOCAL DEV ONLY).

Staff passwords are stored as bcrypt hashes, so a forgotten password cannot be recovered -
you create a new account with a known password instead. The credentials are read from .env
(SEED_MANAGER_EMAIL, SEED_MANAGER_PASSWORD), so no password is hard-coded in source and the
values never reach the repository (.env is gitignored).

Run once against your local DB:

    .venv\\Scripts\\python.exe seed_demo_user.py

Then authenticate at http://127.0.0.1:8000/docs ("Authorize") or via POST /auth/login.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app.database.session import SessionLocal
from app.models.gym import Gym
from app.models.staff import Staff, RoleEnum
from app.core.security import hash_password

EMAIL = os.getenv("SEED_MANAGER_EMAIL", "manager@demo.com")
PASSWORD = os.getenv("SEED_MANAGER_PASSWORD")
if not PASSWORD:
    raise SystemExit(
        "SEED_MANAGER_PASSWORD is not set. Add SEED_MANAGER_EMAIL and "
        "SEED_MANAGER_PASSWORD to your .env, then re-run."
    )

db = SessionLocal()
try:
    existing = db.query(Staff).filter(Staff.email == EMAIL).first()
    if existing:
        print(f"Manager already exists: {EMAIL} (id={existing.id}, gym_id={existing.gym_id})")
    else:
        gym = db.query(Gym).first()
        if gym is None:
            gym = Gym(name="Demo Gym", location="Demo City")
            db.add(gym)
            db.commit()
            db.refresh(gym)
        staff = Staff(
            name="Demo Manager",
            email=EMAIL,
            phone="0000000001",
            role=RoleEnum.manager,
            gym_id=gym.id,
            hashed_password=hash_password(PASSWORD),
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)
        print(f"Created manager id={staff.id} in gym_id={gym.id}")

    # The password is intentionally not printed; it lives in .env (SEED_MANAGER_PASSWORD).
    print(f"\nLog in with username '{EMAIL}' and the SEED_MANAGER_PASSWORD from your .env.")
finally:
    db.close()
