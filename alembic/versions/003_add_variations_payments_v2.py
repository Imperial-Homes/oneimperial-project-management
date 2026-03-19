"""add variations and payments tables v2

Revision ID: add_variations_payments_v2
Revises: add_timeline_id_002
Create Date: 2025-11-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Create project_variations and project_payments tables properly."""
    
    # Create enum types using proper Alembic enum creation
    variation_type_enum = postgresql.ENUM(
        'scope_change', 'design_change', 'unforeseen', 
        'client_request', 'cost_saving', 'regulatory',
        name='variationtype',
        create_type=False
    )
    variation_type_enum.create(op.get_bind(), checkfirst=True)
    
    variation_status_enum = postgresql.ENUM(
        'draft', 'submitted', 'under_review', 'approved', 
        'rejected', 'implemented', 'cancelled',
        name='variationstatus',
        create_type=False
    )
    variation_status_enum.create(op.get_bind(), checkfirst=True)
    
    payment_method_enum = postgresql.ENUM(
        'bank_transfer', 'check', 'cash', 'mobile_money', 
        'wire_transfer', 'credit_card',
        name='paymentmethod',
        create_type=False
    )
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    
    payment_type_enum = postgresql.ENUM(
        'advance', 'milestone', 'progress', 'retention', 'final', 'variation',
        name='paymenttype',
        create_type=False
    )
    payment_type_enum.create(op.get_bind(), checkfirst=True)
    
    payment_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded',
        name='paymentstatus',
        create_type=False
    )
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create project_variations table using Alembic operations
    op.create_table(
        'project_variations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('variation_number', sa.String(50), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('variation_type', variation_type_enum, nullable=False),
        sa.Column('status', variation_status_enum, nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_date', sa.Date, nullable=False),
        sa.Column('original_amount', sa.Numeric(15, 2)),
        sa.Column('variation_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('new_total_amount', sa.Numeric(15, 2)),
        sa.Column('currency', sa.String(3)),
        sa.Column('impact_on_timeline', sa.Integer),
        sa.Column('original_completion_date', sa.Date),
        sa.Column('new_completion_date', sa.Date),
        sa.Column('justification', sa.Text),
        sa.Column('impact_assessment', sa.Text),
        sa.Column('attachments', sa.Text),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('approved_date', sa.Date),
        sa.Column('rejection_reason', sa.Text),
        sa.Column('phase_id', postgresql.UUID(as_uuid=True)),
        sa.Column('task_id', postgresql.UUID(as_uuid=True)),
        sa.Column('priority', sa.String(20)),
        sa.Column('is_active', sa.Boolean),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Create project_payments table using Alembic operations
    op.create_table(
        'project_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('payment_number', sa.String(50), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payment_date', sa.Date, nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3)),
        sa.Column('payment_method', payment_method_enum, nullable=False),
        sa.Column('payment_type', payment_type_enum, nullable=False),
        sa.Column('status', payment_status_enum, nullable=False),
        sa.Column('milestone_id', postgresql.UUID(as_uuid=True)),
        sa.Column('variation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('invoice_reference', sa.String(100)),
        sa.Column('reference_number', sa.String(100)),
        sa.Column('transaction_id', sa.String(100)),
        sa.Column('description', sa.Text),
        sa.Column('notes', sa.Text),
        sa.Column('paid_by', postgresql.UUID(as_uuid=True)),
        sa.Column('paid_by_name', sa.String(255)),
        sa.Column('received_by', postgresql.UUID(as_uuid=True)),
        sa.Column('received_by_name', sa.String(255)),
        sa.Column('receipt_url', sa.String(500)),
        sa.Column('attachments', sa.Text),
        sa.Column('bank_name', sa.String(255)),
        sa.Column('account_number', sa.String(100)),
        sa.Column('is_reconciled', sa.Boolean),
        sa.Column('reconciled_date', sa.Date),
        sa.Column('reconciled_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_project_variations_variation_number', 'project_variations', ['variation_number'], unique=True)
    op.create_index('ix_project_variations_project_id', 'project_variations', ['project_id'])
    op.create_index('ix_project_variations_variation_type', 'project_variations', ['variation_type'])
    op.create_index('ix_project_variations_status', 'project_variations', ['status'])
    
    op.create_index('ix_project_payments_payment_number', 'project_payments', ['payment_number'], unique=True)
    op.create_index('ix_project_payments_project_id', 'project_payments', ['project_id'])
    op.create_index('ix_project_payments_payment_date', 'project_payments', ['payment_date'])
    op.create_index('ix_project_payments_payment_type', 'project_payments', ['payment_type'])
    op.create_index('ix_project_payments_status', 'project_payments', ['status'])
    op.create_index('ix_project_payments_reference_number', 'project_payments', ['reference_number'])


def downgrade():
    """Drop project_variations and project_payments tables."""
    # Drop indexes
    op.drop_index('ix_project_payments_reference_number', table_name='project_payments')
    op.drop_index('ix_project_payments_status', table_name='project_payments')
    op.drop_index('ix_project_payments_payment_type', table_name='project_payments')
    op.drop_index('ix_project_payments_payment_date', table_name='project_payments')
    op.drop_index('ix_project_payments_project_id', table_name='project_payments')
    op.drop_index('ix_project_payments_payment_number', table_name='project_payments')
    
    op.drop_index('ix_project_variations_status', table_name='project_variations')
    op.drop_index('ix_project_variations_variation_type', table_name='project_variations')
    op.drop_index('ix_project_variations_project_id', table_name='project_variations')
    op.drop_index('ix_project_variations_variation_number', table_name='project_variations')
    
    # Drop tables
    op.drop_table('project_payments')
    op.drop_table('project_variations')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS variationstatus')
    op.execute('DROP TYPE IF EXISTS variationtype')
