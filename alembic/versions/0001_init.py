"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'attorney', 'paralegal', 'viewer')")
    op.execute("CREATE TYPE case_status AS ENUM ('draft', 'active', 'archived', 'deleted')")
    op.execute("CREATE TYPE evidence_status AS ENUM ('uploaded', 'processing', 'processed', 'failed', 'locked')")
    op.execute("CREATE TYPE storyboard_status AS ENUM ('draft', 'validating', 'validated', 'compiling', 'compiled', 'failed')")
    op.execute("CREATE TYPE render_status AS ENUM ('queued', 'rendering', 'completed', 'failed', 'cancelled')")
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'attorney', 'paralegal', 'viewer', name='user_role'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create cases table
    op.create_table('cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('case_number', sa.String(length=100), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'archived', 'deleted', name='case_status'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('case_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_number')
    )
    
    # Create evidence table
    op.create_table('evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('status', postgresql.ENUM('uploaded', 'processing', 'processed', 'failed', 'locked', name='evidence_status'), nullable=True),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('case_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('processing_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create storyboards table
    op.create_table('storyboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'validating', 'validated', 'compiling', 'compiled', 'failed', name='storyboard_status'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('compiled_at', sa.DateTime(), nullable=True),
        sa.Column('case_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scenes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timeline_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('render_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create renders table
    op.create_table('renders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storyboard_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('queued', 'rendering', 'completed', 'failed', 'cancelled', name='render_status'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('render_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('case_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['storyboard_id'], ['storyboards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create export_jobs table
    op.create_table('export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('case_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_cases_case_number', 'cases', ['case_number'], unique=True)
    op.create_index('ix_cases_created_by', 'cases', ['created_by'])
    op.create_index('ix_cases_status', 'cases', ['status'])
    op.create_index('ix_evidence_case_id', 'evidence', ['case_id'])
    op.create_index('ix_evidence_uploaded_by', 'evidence', ['uploaded_by'])
    op.create_index('ix_evidence_status', 'evidence', ['status'])
    op.create_index('ix_evidence_file_hash', 'evidence', ['file_hash'])
    op.create_index('ix_storyboards_case_id', 'storyboards', ['case_id'])
    op.create_index('ix_storyboards_created_by', 'storyboards', ['created_by'])
    op.create_index('ix_storyboards_status', 'storyboards', ['status'])
    op.create_index('ix_renders_case_id', 'renders', ['case_id'])
    op.create_index('ix_renders_storyboard_id', 'renders', ['storyboard_id'])
    op.create_index('ix_renders_created_by', 'renders', ['created_by'])
    op.create_index('ix_renders_status', 'renders', ['status'])
    op.create_index('ix_export_jobs_case_id', 'export_jobs', ['case_id'])
    op.create_index('ix_export_jobs_created_by', 'export_jobs', ['created_by'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_export_jobs_created_by', table_name='export_jobs')
    op.drop_index('ix_export_jobs_case_id', table_name='export_jobs')
    op.drop_index('ix_renders_status', table_name='renders')
    op.drop_index('ix_renders_created_by', table_name='renders')
    op.drop_index('ix_renders_storyboard_id', table_name='renders')
    op.drop_index('ix_renders_case_id', table_name='renders')
    op.drop_index('ix_storyboards_status', table_name='storyboards')
    op.drop_index('ix_storyboards_created_by', table_name='storyboards')
    op.drop_index('ix_storyboards_case_id', table_name='storyboards')
    op.drop_index('ix_evidence_file_hash', table_name='evidence')
    op.drop_index('ix_evidence_status', table_name='evidence')
    op.drop_index('ix_evidence_uploaded_by', table_name='evidence')
    op.drop_index('ix_evidence_case_id', table_name='evidence')
    op.drop_index('ix_cases_status', table_name='cases')
    op.drop_index('ix_cases_created_by', table_name='cases')
    op.drop_index('ix_cases_case_number', table_name='cases')
    op.drop_index('ix_users_email', table_name='users')
    
    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('export_jobs')
    op.drop_table('renders')
    op.drop_table('storyboards')
    op.drop_table('evidence')
    op.drop_table('cases')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute("DROP TYPE render_status")
    op.execute("DROP TYPE storyboard_status")
    op.execute("DROP TYPE evidence_status")
    op.execute("DROP TYPE case_status")
    op.execute("DROP TYPE user_role")
