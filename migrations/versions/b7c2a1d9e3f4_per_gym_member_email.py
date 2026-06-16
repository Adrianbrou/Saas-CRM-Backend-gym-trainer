"""per-gym member email; drop incorrect global unique constraints

Revision ID: b7c2a1d9e3f4
Revises: 3ec3cf30bfe6
Create Date: 2026-06-14 14:00:00.000000

Members now enforce email uniqueness PER GYM via a composite unique constraint
(gym_id, email) instead of a global unique - two gyms may share a member email.
The incorrect global uniques on members.phone and on staff.name / staff.phone are
dropped. staff.email stays globally unique because staff authenticate by email and
login must stay unambiguous.

NOTE on object types (verified against the real Postgres schema): columns declared with
`index=True, unique=True` produced a UNIQUE INDEX (ix_<table>_<column>), so they are
dropped with drop_index and recreated as a plain (non-unique) index. The column declared
with `unique=True` only (members.phone) produced a UNIQUE CONSTRAINT (members_phone_key),
so it is dropped with drop_constraint.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c2a1d9e3f4'
down_revision: Union[str, Sequence[str], None] = '3ec3cf30bfe6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Members: email unique per gym (composite), no longer globally unique; phone not unique.
    op.drop_index('ix_members_email', table_name='members')
    op.create_index('ix_members_email', 'members', ['email'], unique=False)
    op.drop_constraint('members_phone_key', 'members', type_='unique')
    op.create_unique_constraint('uq_member_gym_email', 'members', ['gym_id', 'email'])

    # Staff: drop the incorrect global uniques on name and phone (they were unique indexes).
    # staff.email stays unique - it is the login identity.
    op.drop_index('ix_staff_name', table_name='staff')
    op.create_index('ix_staff_name', 'staff', ['name'], unique=False)
    op.drop_index('ix_staff_phone', table_name='staff')
    op.create_index('ix_staff_phone', 'staff', ['phone'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_staff_phone', table_name='staff')
    op.create_index('ix_staff_phone', 'staff', ['phone'], unique=True)
    op.drop_index('ix_staff_name', table_name='staff')
    op.create_index('ix_staff_name', 'staff', ['name'], unique=True)

    op.drop_constraint('uq_member_gym_email', 'members', type_='unique')
    op.create_unique_constraint('members_phone_key', 'members', ['phone'])
    op.drop_index('ix_members_email', table_name='members')
    op.create_index('ix_members_email', 'members', ['email'], unique=True)
