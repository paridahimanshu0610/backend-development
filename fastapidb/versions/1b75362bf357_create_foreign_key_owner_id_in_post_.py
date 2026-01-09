"""create foreign key owner id in post table

Revision ID: 1b75362bf357
Revises: 4058d2b1ab43
Create Date: 2026-01-09 01:22:44.371132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b75362bf357'
down_revision: Union[str, Sequence[str], None] = '4058d2b1ab43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable first (required if table already has rows)
    op.add_column(
        'post',
        sa.Column('owner_id', sa.Integer(), nullable=True)
    )

    # 2. Create foreign key constraint with ON DELETE CASCADE
    op.create_foreign_key(
        constraint_name='fk_post_owner_id_user',
        source_table='post',
        referent_table='user',
        local_cols=['owner_id'],
        remote_cols=['id'],
        ondelete='CASCADE',
    )

    # 3. Make column NOT NULL
    op.alter_column(
        'post',
        'owner_id',
        nullable=False
    )


def downgrade() -> None:
    # Drop FK first (required by PostgreSQL)
    op.drop_constraint(
        'fk_post_owner_id_user',
        'post',
        type_='foreignkey'
    )

    # Then drop column
    op.drop_column('post', 'owner_id')