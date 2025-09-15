"""Add chain of custody and evidence lock tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chain_of_custody table
    op.create_table('chain_of_custody',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create evidence_lock table
    op.create_table('evidence_lock',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('immutable_at', sa.DateTime(), nullable=False),
        sa.Column('locked_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lock_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ),
        sa.ForeignKeyConstraint(['locked_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('evidence_id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_chain_of_custody_evidence_id', 'chain_of_custody', ['evidence_id'])
    op.create_index('ix_chain_of_custody_timestamp', 'chain_of_custody', ['timestamp'])
    op.create_index('ix_chain_of_custody_action', 'chain_of_custody', ['action'])
    op.create_index('ix_evidence_lock_evidence_id', 'evidence_lock', ['evidence_id'])
    op.create_index('ix_evidence_lock_immutable_at', 'evidence_lock', ['immutable_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_evidence_lock_immutable_at', table_name='evidence_lock')
    op.drop_index('ix_evidence_lock_evidence_id', table_name='evidence_lock')
    op.drop_index('ix_chain_of_custody_action', table_name='chain_of_custody')
    op.drop_index('ix_chain_of_custody_timestamp', table_name='chain_of_custody')
    op.drop_index('ix_chain_of_custody_evidence_id', table_name='chain_of_custody')
    
    # Drop tables
    op.drop_table('evidence_lock')
    op.drop_table('chain_of_custody')
