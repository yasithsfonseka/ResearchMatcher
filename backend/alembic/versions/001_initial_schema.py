"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-06 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from app.core.config import settings

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    res = conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector';")).fetchone()
    has_vector = res is not None

    if has_vector:
        from pgvector.sqlalchemy import Vector
        embedding_col_type = Vector(settings.EMBEDDING_DIMENSION)
    else:
        embedding_col_type = sa.JSON()
    
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # papers
    op.create_table(
        'papers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('canonical_title', sa.Text(), nullable=False),
        sa.Column('normalized_title', sa.Text(), nullable=False),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=500), nullable=True),
        sa.Column('work_type', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doi')
    )
    op.create_index(op.f('ix_papers_doi'), 'papers', ['doi'], unique=True)
    op.create_index(op.f('ix_papers_normalized_title'), 'papers', ['normalized_title'], unique=False)
    op.create_index(op.f('ix_papers_publication_year'), 'papers', ['publication_year'], unique=False)

    # authors
    op.create_table(
        'authors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('orcid', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('orcid')
    )
    op.create_index(op.f('ix_authors_display_name'), 'authors', ['display_name'], unique=False)

    # paper_authors
    op.create_table(
        'paper_authors',
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('author_id', sa.String(length=36), nullable=False),
        sa.Column('author_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id', 'author_id')
    )

    # paper_source_records
    op.create_table(
        'paper_source_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('original_url', sa.Text(), nullable=False),
        sa.Column('open_access_url', sa.Text(), nullable=True),
        sa.Column('access_status', sa.String(length=100), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=True),
        sa.Column('provider_updated_at', sa.DateTime(), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('provenance_info', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'external_id', name='uq_provider_external_id')
    )

    # subjects
    op.create_table(
        'subjects',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('parent_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['subjects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'external_id', name='uq_subject_provider_external')
    )
    op.create_index(op.f('ix_subjects_name'), 'subjects', ['name'], unique=False)

    # paper_subjects
    op.create_table(
        'paper_subjects',
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('subject_id', sa.String(length=36), nullable=False),
        sa.Column('assignment_method', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('paper_id', 'subject_id')
    )

    # paper_embeddings
    op.create_table(
        'paper_embeddings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('model_id', sa.String(length=255), nullable=False),
        sa.Column('model_revision', sa.String(length=100), nullable=False),
        sa.Column('input_hash', sa.String(length=64), nullable=False),
        sa.Column('embedding', embedding_col_type, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'model_id', 'input_hash', name='uq_paper_model_hash')
    )

    # collections
    op.create_table(
        'collections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # collection_papers
    op.create_table(
        'collection_papers',
        sa.Column('collection_id', sa.String(length=36), nullable=False),
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('reading_status', sa.String(length=50), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('collection_id', 'paper_id')
    )

    # search_runs
    op.create_table(
        'search_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('research_title', sa.Text(), nullable=False),
        sa.Column('research_description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('subject_filters', sa.JSON(), nullable=True),
        sa.Column('year_min', sa.Integer(), nullable=True),
        sa.Column('year_max', sa.Integer(), nullable=True),
        sa.Column('open_access_only', sa.Boolean(), nullable=True),
        sa.Column('ranking_config', sa.JSON(), nullable=True),
        sa.Column('provider_status', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # search_results
    op.create_table(
        'search_results',
        sa.Column('search_run_id', sa.String(length=36), nullable=False),
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('keyword_score', sa.Float(), nullable=False),
        sa.Column('semantic_score', sa.Float(), nullable=False),
        sa.Column('subject_score', sa.Float(), nullable=False),
        sa.Column('final_score', sa.Float(), nullable=False),
        sa.Column('explanation_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['search_run_id'], ['search_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('search_run_id', 'paper_id')
    )

    # relevance_feedback
    op.create_table(
        'relevance_feedback',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('search_run_id', sa.String(length=36), nullable=False),
        sa.Column('paper_id', sa.String(length=36), nullable=False),
        sa.Column('relevance_judgment', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['search_run_id'], ['search_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ingestion_jobs
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('ingestion_jobs')
    op.drop_table('relevance_feedback')
    op.drop_table('search_results')
    op.drop_table('search_runs')
    op.drop_table('collection_papers')
    op.drop_table('collections')
    op.drop_table('paper_embeddings')
    op.drop_table('paper_subjects')
    op.drop_table('subjects')
    op.drop_table('paper_source_records')
    op.drop_table('paper_authors')
    op.drop_table('authors')
    op.drop_table('papers')
    op.drop_table('users')
