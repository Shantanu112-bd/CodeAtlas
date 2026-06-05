"""Create repositories table

Revision ID: 002_create_repositories_table
Revises: 001_create_users_table
Create Date: 2026-06-05T17:00:44

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_create_repositories_table'
down_revision: Union[str, None] = '001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    repository_status_enum = sa.Enum('PENDING', 'CLONING', 'INDEXED', 'FAILED', name='repositorystatus')
    repository_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_url', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner', sa.String(), nullable=False),
        sa.Column('default_branch', sa.String(), server_default='main', nullable=False),
        sa.Column('local_path', sa.String(), nullable=False),
        sa.Column('status', repository_status_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_repositories_github_url'), 'repositories', ['github_url'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('idx_repositories_github_url'), table_name='repositories')
    op.drop_table('repositories')
    sa.Enum(name='repositorystatus').drop(op.get_bind(), checkfirst=True)
