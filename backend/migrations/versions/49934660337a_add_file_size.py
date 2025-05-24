"""add file size

Revision ID: 49934660337a
Revises: e0bd27b45511
Create Date: 2025-05-14 14:12:55.938104

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "49934660337a"
down_revision: Union[str, None] = "e0bd27b45511"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "files",
        sa.Column("size", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("files", "size")
