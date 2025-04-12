"""Add privacy column to files table

Revision ID: 0717d5a6c01c
Revises: 8c333bd16ac7
Create Date: 2025-04-12 21:05:44.216106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0717d5a6c01c'
down_revision: Union[str, None] = '8c333bd16ac7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the old 'is_public' column
    op.drop_column('files', 'is_public')    
    
    # Add 'privacy' column to 'files' table
    op.add_column('files', sa.Column('privacy', sa.Enum('private', 'protected', 'public'), nullable=True))

    # Add 'shared_to' column to 'files' table (as TEXT for JSON storage in SQLite)
    op.add_column('files', sa.Column('shared_to', sa.TEXT, nullable=True))

    # Create 'shared_files' table
    op.create_table(
        'shared_files',
        sa.Column('file_id', sa.String(length=36), sa.ForeignKey('files.id'), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), primary_key=True)
    )


def downgrade() -> None:
    # Drop 'shared_files' table
    op.drop_table('shared_files')

    # Drop 'shared_to' column from 'files' table
    op.drop_column('files', 'shared_to')

    # Drop 'privacy' column from 'files' table
    op.drop_column('files', 'privacy')

    # bring back the 'is_public' column
    op.add_column('files', sa.Column('is_public', sa.BOOLEAN(), nullable=False, default=False))
