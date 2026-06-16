from app.database.base import Base
from sqlalchemy import Column, Integer, func, DateTime, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

import enum


class RoleEnum(str, enum.Enum):
    manager = "manager"
    trainer = "trainer"
    # office = "office"
    # receptionist = "receptionist"
    # admin = "admin"


class Staff(Base):

    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    role = Column(Enum(RoleEnum), nullable=False)
    name = Column(String, nullable=False, index=True)
    # Staff authenticate by email globally (see auth.login), so staff email stays
    # globally unique to keep login unambiguous. Name and phone are not unique.
    email = Column(String, nullable=False, index=True, unique=True)
    phone = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)

    # foreign key from the gym
    gym_id = Column(Integer,
                    ForeignKey("gyms.id", ondelete="CASCADE"),
                    nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships: 1 gym, 2 members
    gym = relationship("Gym", back_populates="staff")
    sessions = relationship(
        "WorkoutSession", back_populates="staff", cascade="all, delete")
