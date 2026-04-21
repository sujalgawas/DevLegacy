"""fix

Revision ID: 72f18f961f0f
Revises: 43397b5a2132
Create Date: 2026-04-21 03:47:37.044052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '72f18f961f0f'
down_revision: Union[str, Sequence[str], None] = '43397b5a2132'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Convert recommended_role -> JSONB safely
    op.execute("""
        ALTER TABLE github_profile
        ALTER COLUMN recommended_role
        TYPE JSONB
        USING to_jsonb(recommended_role)
    """)

    # Convert detected_frameworks -> JSONB safely
    op.execute("""
        ALTER TABLE github_profile
        ALTER COLUMN detected_frameworks
        TYPE JSONB
        USING to_jsonb(detected_frameworks)
    """)


def downgrade() -> None:
    """Downgrade schema."""

    # Convert JSONB back to VARCHAR
    op.execute("""
        ALTER TABLE github_profile
        ALTER COLUMN detected_frameworks
        TYPE VARCHAR
        USING detected_frameworks::text
    """)

    op.execute("""
        ALTER TABLE github_profile
        ALTER COLUMN recommended_role
        TYPE VARCHAR
        USING recommended_role::text
    """)