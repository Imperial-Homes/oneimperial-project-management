"""add variations and payments tables

Revision ID: add_variations_payments_001
Revises: 
Create Date: 2025-11-06 00:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create project_variations and project_payments tables."""
    
    # Create enum types (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE variationtype AS ENUM (
                'scope_change', 'design_change', 'unforeseen', 
                'client_request', 'cost_saving', 'regulatory'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE variationstatus AS ENUM (
                'draft', 'submitted', 'under_review', 'approved', 
                'rejected', 'implemented', 'cancelled'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentmethod AS ENUM (
                'bank_transfer', 'check', 'cash', 'mobile_money', 
                'wire_transfer', 'credit_card'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymenttype AS ENUM (
                'advance', 'milestone', 'progress', 'retention', 'final', 'variation'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE paymentstatus AS ENUM (
                'pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create project_variations table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_variations (
            id UUID PRIMARY KEY,
            variation_number VARCHAR(50) UNIQUE NOT NULL,
            project_id UUID NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            variation_type variationtype NOT NULL,
            status variationstatus NOT NULL,
            requested_by UUID NOT NULL,
            requested_date DATE NOT NULL,
            original_amount NUMERIC(15, 2),
            variation_amount NUMERIC(15, 2) NOT NULL,
            new_total_amount NUMERIC(15, 2),
            currency VARCHAR(3),
            impact_on_timeline INTEGER,
            original_completion_date DATE,
            new_completion_date DATE,
            justification TEXT,
            impact_assessment TEXT,
            attachments TEXT,
            approved_by UUID,
            approved_date DATE,
            rejection_reason TEXT,
            phase_id UUID,
            task_id UUID,
            priority VARCHAR(20),
            is_active BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_by UUID,
            updated_at TIMESTAMP WITH TIME ZONE,
            updated_by UUID
        )
    """)
    
    # Create project_payments table (if not exists)
    op.execute("""
        CREATE TABLE IF NOT EXISTS project_payments (
            id UUID PRIMARY KEY,
            payment_number VARCHAR(50) UNIQUE NOT NULL,
            project_id UUID NOT NULL,
            payment_date DATE NOT NULL,
            amount NUMERIC(15, 2) NOT NULL,
            currency VARCHAR(3),
            payment_method paymentmethod NOT NULL,
            payment_type paymenttype NOT NULL,
            status paymentstatus NOT NULL,
            milestone_id UUID,
            variation_id UUID,
            invoice_reference VARCHAR(100),
            reference_number VARCHAR(100),
            transaction_id VARCHAR(100),
            description TEXT,
            notes TEXT,
            paid_by UUID,
            paid_by_name VARCHAR(255),
            received_by UUID,
            received_by_name VARCHAR(255),
            receipt_url VARCHAR(500),
            attachments TEXT,
            bank_name VARCHAR(255),
            account_number VARCHAR(100),
            is_reconciled BOOLEAN,
            reconciled_date DATE,
            reconciled_by UUID,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_by UUID,
            updated_at TIMESTAMP WITH TIME ZONE,
            updated_by UUID
        )
    """)
    
    # Create indexes (if not exists)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_project_variations_variation_number ON project_variations(variation_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_variations_project_id ON project_variations(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_variations_variation_type ON project_variations(variation_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_variations_status ON project_variations(status)")
    
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_project_payments_payment_number ON project_payments(payment_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_payments_project_id ON project_payments(project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_payments_payment_date ON project_payments(payment_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_payments_payment_type ON project_payments(payment_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_payments_status ON project_payments(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_project_payments_reference_number ON project_payments(reference_number)")
    
    # Create foreign keys (if not exists)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE project_variations ADD CONSTRAINT fk_project_variations_project_id 
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE project_payments ADD CONSTRAINT fk_project_payments_project_id 
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)


def downgrade():
    """Drop project_variations and project_payments tables."""
    op.drop_constraint('fk_project_payments_project_id', 'project_payments', type_='foreignkey')
    op.drop_constraint('fk_project_variations_project_id', 'project_variations', type_='foreignkey')
    
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
    
    op.drop_table('project_payments')
    op.drop_table('project_variations')
    
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymenttype')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS variationstatus')
    op.execute('DROP TYPE IF EXISTS variationtype')
