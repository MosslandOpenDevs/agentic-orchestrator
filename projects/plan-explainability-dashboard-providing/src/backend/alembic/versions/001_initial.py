"""Initial migration

Revision ID: 001
Create Date: Auto-generated

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tables based on models
    # This is a placeholder - run alembic revision --autogenerate
    pass


def downgrade() -> None:
    # Drop tables
    pass
