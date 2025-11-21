"""rename payments to payment certificates

Revision ID: rename_to_payment_certificates
Revises: add_variations_payments_v2
Create Date: 2025-11-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rename_to_payment_certificates'
down_revision = 'add_variations_payments_v2'
branch_labels = None
depends_on = None


def upgrade():
    """Rename project_payments to payment_certificates and update structure."""
    
    # Drop old table if exists
    op.execute('DROP TABLE IF EXISTS project_payments CASCADE')
    
    # Drop old enum types
    op.execute('DROP TYPE IF EXISTS paymentstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS paymenttype CASCADE')
    op.execute('DROP TYPE IF EXISTS paymentmethod CASCADE')
    
    # Create new enum types for certificates
    certificate_status_enum = postgresql.ENUM(
        'draft', 'submitted', 'approved', 'rejected', 'paid', 'partially_paid',
        name='certificatestatus',
        create_type=False
    )
    certificate_status_enum.create(op.get_bind(), checkfirst=True)
    
    certificate_type_enum = postgresql.ENUM(
        'interim', 'advance', 'retention', 'final', 'variation',
        name='certificatetype',
        create_type=False
    )
    certificate_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create payment_certificates table
    op.create_table(
        'payment_certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('certificate_number', sa.String(50), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certificate_date', sa.Date, nullable=False),
        sa.Column('certificate_type', certificate_type_enum, nullable=False),
        sa.Column('status', certificate_status_enum, nullable=False),
        sa.Column('gross_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('previous_amount', sa.Numeric(15, 2), server_default='0'),
        sa.Column('current_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('retention_percentage', sa.Numeric(5, 2), server_default='5.0'),
        sa.Column('retention_amount', sa.Numeric(15, 2), server_default='0'),
        sa.Column('net_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='GHS'),
        sa.Column('period_from', sa.Date),
        sa.Column('period_to', sa.Date),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True)),
        sa.Column('variation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text),
        sa.Column('work_completed', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('submitted_date', sa.Date),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True)),
        sa.Column('approved_date', sa.Date),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('rejected_date', sa.Date),
        sa.Column('rejected_by', postgresql.UUID(as_uuid=True)),
        sa.Column('rejection_reason', sa.Text),
        sa.Column('payment_date', sa.Date),
        sa.Column('payment_reference', sa.String(100)),
        sa.Column('amount_paid', sa.Numeric(15, 2), server_default='0'),
        sa.Column('consultant_name', sa.String(255)),
        sa.Column('contractor_name', sa.String(255)),
        sa.Column('client_name', sa.String(255)),
        sa.Column('attachments', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_payment_certificates_certificate_number', 'payment_certificates', ['certificate_number'], unique=True)
    op.create_index('ix_payment_certificates_project_id', 'payment_certificates', ['project_id'])
    op.create_index('ix_payment_certificates_certificate_date', 'payment_certificates', ['certificate_date'])
    op.create_index('ix_payment_certificates_certificate_type', 'payment_certificates', ['certificate_type'])
    op.create_index('ix_payment_certificates_status', 'payment_certificates', ['status'])


def downgrade():
    """Revert back to project_payments."""
    # Drop indexes
    op.drop_index('ix_payment_certificates_status', table_name='payment_certificates')
    op.drop_index('ix_payment_certificates_certificate_type', table_name='payment_certificates')
    op.drop_index('ix_payment_certificates_certificate_date', table_name='payment_certificates')
    op.drop_index('ix_payment_certificates_project_id', table_name='payment_certificates')
    op.drop_index('ix_payment_certificates_certificate_number', table_name='payment_certificates')
    
    # Drop table
    op.drop_table('payment_certificates')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS certificatetype')
    op.execute('DROP TYPE IF EXISTS certificatestatus')
