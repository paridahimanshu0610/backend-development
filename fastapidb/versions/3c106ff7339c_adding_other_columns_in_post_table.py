"""adding other columns in post table

Revision ID: 3c106ff7339c
Revises: 8c174c62ed52
Create Date: 2026-01-09 01:02:13.823888

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3c106ff7339c'
down_revision: Union[str, Sequence[str], None] = '8c174c62ed52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'post',
        sa.Column(
            'published',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        )
    )
    op.add_column(
        'post',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('post', 'published')
    op.drop_column('post', 'created_at')
