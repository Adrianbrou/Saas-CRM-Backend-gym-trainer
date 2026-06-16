from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, UniqueConstraint
from app.database.base import Base
from sqlalchemy.orm import relationship


class Member(Base):
    """
    create 


    """

    # create the table name
    __tablename__ = "members"

    # Email is unique PER GYM, not globally: two different gyms may each have a member
    # with the same email. Members do not authenticate, so a global unique would wrongly
    # couple separate tenants. Enforced as a composite constraint instead of unique=True.
    __table_args__ = (
        UniqueConstraint("gym_id", "email", name="uq_member_gym_email"),
    )

    # members id
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)

    # create the foreign key from the gym table
    gym_id = Column(Integer,
                    ForeignKey("gyms.id", ondelete="CASCADE"),
                    nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # relationship
    """_summary_: the "Gym" is the class name, and "members" is the relationship name in the "Gym" class
        Child table : no cascade
    """
    gym = relationship(
        "Gym", back_populates="members")
    # From progress(child) :-> Member(parents):
    progress_logs = relationship(
        "Progress", back_populates="member", cascade="all, delete")
