"""
seed_demo_user.py - create a known manager you can log in with (LOCAL DEV ONLY).

Staff passwords are stored as bcrypt hashes, so a forgotten password cannot be recovered -
you create a new account with a known password instead. Run this once against your local DB:

    .venv\\Scripts\\python.exe seed_demo_user.py

Then authenticate at http://127.0.0.1:8000/docs (the "Authorize" button) or via the API:

    username: manager@demo.com
    password: demo12345
"""

from app.database.session import SessionLocal
from app.models.gym import Gym
from app.models.staff import Staff, RoleEnum
from app.core.security import hash_password

EMAIL = "manager@demo.com"
PASSWORD = "demo12345"

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

    print("\nLog in with:")
    print(f"  username: {EMAIL}")
    print(f"  password: {PASSWORD}")
finally:
    db.close()
