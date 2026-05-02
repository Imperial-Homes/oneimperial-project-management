"""Add interior_decor_status, client_access_link, sinking_fund_payment_status, letter_to_client_url to handover_packs."""

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column("handover_packs", sa.Column("interior_decor_status", sa.String(100), nullable=True))
    op.add_column("handover_packs", sa.Column("client_access_link", sa.Text(), nullable=True))
    op.add_column("handover_packs", sa.Column("sinking_fund_payment_status", sa.String(50), nullable=True))
    op.add_column("handover_packs", sa.Column("letter_to_client_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("handover_packs", "letter_to_client_url")
    op.drop_column("handover_packs", "sinking_fund_payment_status")
    op.drop_column("handover_packs", "client_access_link")
    op.drop_column("handover_packs", "interior_decor_status")
