"""add project incidents table

Revision ID: add_project_incidents
Revises: rename_to_payment_certificates
Create Date: 2025-11-21 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_project_incidents'
down_revision = 'rename_to_payment_certificates'
branch_labels = None
depends_on = None


def upgrade():
    """Create project_incidents table."""
    
    # Create enum types
    incident_severity_enum = postgresql.ENUM(
        'minor', 'moderate', 'major', 'critical',
        name='incidentseverity',
        create_type=False
    )
    incident_severity_enum.create(op.get_bind(), checkfirst=True)
    
    incident_status_enum = postgresql.ENUM(
        'investigating', 'in_recovery', 'resolved', 'closed',
        name='incidentstatus',
        create_type=False
    )
    incident_status_enum.create(op.get_bind(), checkfirst=True)
    
    incident_type_enum = postgresql.ENUM(
        'safety', 'quality', 'security', 'environmental', 
        'equipment', 'delay', 'accident', 'other',
        name='incidenttype',
        create_type=False
    )
    incident_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create project_incidents table
    op.create_table(
        'project_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_number', sa.String(50), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_type', incident_type_enum, nullable=False),
        sa.Column('severity', incident_severity_enum, nullable=False),
        sa.Column('status', incident_status_enum, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('location', sa.String(255)),
        sa.Column('incident_date', sa.Date, nullable=False),
        sa.Column('reported_date', sa.Date, nullable=False),
        sa.Column('reported_by', postgresql.UUID(as_uuid=True)),
        sa.Column('reported_by_name', sa.String(255)),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('assigned_to_name', sa.String(255)),
        sa.Column('injuries_count', sa.String(50)),
        sa.Column('property_damage', sa.String(255)),
        sa.Column('work_stoppage_hours', sa.String(50)),
        sa.Column('estimated_cost', sa.String(100)),
        sa.Column('root_cause', sa.Text),
        sa.Column('corrective_actions', sa.Text),
        sa.Column('preventive_measures', sa.Text),
        sa.Column('resolved_date', sa.Date),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('attachments', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('requires_investigation', sa.Boolean, server_default='true'),
        sa.Column('investigation_completed', sa.Boolean, server_default='false'),
        sa.Column('follow_up_required', sa.Boolean, server_default='false'),
        sa.Column('follow_up_date', sa.Date),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_project_incidents_incident_number', 'project_incidents', ['incident_number'], unique=True)
    op.create_index('ix_project_incidents_project_id', 'project_incidents', ['project_id'])
    op.create_index('ix_project_incidents_incident_type', 'project_incidents', ['incident_type'])
    op.create_index('ix_project_incidents_severity', 'project_incidents', ['severity'])
    op.create_index('ix_project_incidents_status', 'project_incidents', ['status'])
    op.create_index('ix_project_incidents_incident_date', 'project_incidents', ['incident_date'])


def downgrade():
    """Drop project_incidents table."""
    # Drop indexes
    op.drop_index('ix_project_incidents_incident_date', table_name='project_incidents')
    op.drop_index('ix_project_incidents_status', table_name='project_incidents')
    op.drop_index('ix_project_incidents_severity', table_name='project_incidents')
    op.drop_index('ix_project_incidents_incident_type', table_name='project_incidents')
    op.drop_index('ix_project_incidents_project_id', table_name='project_incidents')
    op.drop_index('ix_project_incidents_incident_number', table_name='project_incidents')
    
    # Drop table
    op.drop_table('project_incidents')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS incidenttype')
    op.execute('DROP TYPE IF EXISTS incidentstatus')
    op.execute('DROP TYPE IF EXISTS incidentseverity')
