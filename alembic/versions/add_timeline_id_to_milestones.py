"""add timeline_id to timeline_milestones

Revision ID: add_timeline_id_002
Revises: add_variations_payments_001
Create Date: 2025-11-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_timeline_id_002'
down_revision = 'add_variations_payments_001'
branch_labels = None
depends_on = None


def upgrade():
    """Add timeline_id column to timeline_milestones table."""
    
    # Add timeline_id column (nullable to allow existing data)
    op.execute("""
        DO $ BEGIN
            ALTER TABLE timeline_milestones 
            ADD COLUMN IF NOT EXISTS timeline_id UUID;
        EXCEPTION
            WHEN duplicate_column THEN null;
        END $;
    """)
    
    # Create index on timeline_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_timeline_milestones_timeline_id 
        ON timeline_milestones(timeline_id)
    """)
    
    # Add foreign key constraint
    op.execute("""
        DO $ BEGIN
            ALTER TABLE timeline_milestones 
            ADD CONSTRAINT fk_timeline_milestones_timeline_id 
            FOREIGN KEY (timeline_id) REFERENCES project_timelines(id) ON DELETE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $;
    """)


def downgrade():
    """Remove timeline_id column from timeline_milestones table."""
    
    # Drop foreign key constraint
    op.execute("""
        ALTER TABLE timeline_milestones 
        DROP CONSTRAINT IF EXISTS fk_timeline_milestones_timeline_id
    """)
    
    # Drop index
    op.execute("""
        DROP INDEX IF EXISTS ix_timeline_milestones_timeline_id
    """)
    
    # Drop column
    op.execute("""
        ALTER TABLE timeline_milestones 
        DROP COLUMN IF EXISTS timeline_id
    """)
