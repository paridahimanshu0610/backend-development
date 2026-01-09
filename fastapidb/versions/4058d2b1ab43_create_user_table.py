"""create user table

Revision ID: 4058d2b1ab43
Revises: 3c106ff7339c
Create Date: 2026-01-09 01:18:02.533657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4058d2b1ab43'
down_revision: Union[str, Sequence[str], None] = '3c106ff7339c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column(
            'date_created',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.UniqueConstraint('username', name='uq_user_username'),
        sa.UniqueConstraint('email', name='uq_user_email'),
    )


def downgrade() -> None:
    op.drop_table('user')