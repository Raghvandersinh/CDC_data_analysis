"""clear  stroke_mortality table

Revision ID: d6ed8ea3e9c4
Revises: 2d3f1ef08379
Create Date: 2026-11-10 13:19:13.356661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6ed8ea3e9c4'
down_revision: Union[str, Sequence[str], None] = '2d3f1ef08379'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DELETE FROM stroke_mortality")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
