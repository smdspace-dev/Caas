"""Add enhanced metadata fields to documents table

Revision ID: phase4_enhanced_metadata
Revises: previous_migration
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase4_enhanced_metadata'
down_revision = None  # Update this with the actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced metadata fields to documents table"""
    # Add new columns to documents table
    op.add_column('documents', sa.Column('processing_time', sa.Float(), nullable=True))
    op.add_column('documents', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('document_metadata', sa.JSON(), nullable=True))
    op.add_column('documents', sa.Column('created_at', sa.DateTime(), nullable=True))
    
    # Set default values for created_at using uploaded_at
    op.execute("UPDATE documents SET created_at = uploaded_at WHERE created_at IS NULL")


def downgrade():
    """Remove enhanced metadata fields from documents table"""
    op.drop_column('documents', 'created_at')
    op.drop_column('documents', 'document_metadata')
    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'processing_time')