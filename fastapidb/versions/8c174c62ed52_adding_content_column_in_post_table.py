"""adding content column in post table

Revision ID: 8c174c62ed52
Revises: c70510a6b0b7
Create Date: 2026-01-09 00:27:36.165640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c174c62ed52'
down_revision: Union[str, Sequence[str], None] = 'c70510a6b0b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'post',
        sa.Column('content', sa.String(), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('post', 'content')
