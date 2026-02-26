"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create prediction_status enum
    prediction_status = postgresql.ENUM(
        'scheduled', 'active', 'cancelled', 'archived',
        name='predictionstatus'
    )
    prediction_status.create(op.get_bind())

    # Create media_type enum
    media_type = postgresql.ENUM(
        'photo', 'gif', 'video', 'animation',
        name='mediatype'
    )
    media_type.create(op.get_bind())

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id')
    )
    op.create_index('ix_users_telegram_user_id', 'users', ['telegram_user_id'])

    # Create predictions table
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'active', 'cancelled', 'archived', name='predictionstatus'), nullable=False),
        sa.Column('media_type', sa.Enum('photo', 'gif', 'video', 'animation', name='mediatype'), nullable=False),
        sa.Column('media_file_id', sa.String(255), nullable=False),
        sa.Column('post_text', sa.Text(), nullable=False),
        sa.Column('button_1_initial', sa.String(64), nullable=False),
        sa.Column('button_2_initial', sa.String(64), nullable=False),
        sa.Column('button_3_initial', sa.String(64), nullable=False),
        sa.Column('button_1_final', sa.String(64), nullable=False),
        sa.Column('button_2_final', sa.String(64), nullable=False),
        sa.Column('button_3_final', sa.String(64), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('broadcast_started', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('broadcast_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_admin_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create partial unique indexes for predictions
    op.execute("""
        CREATE UNIQUE INDEX ix_predictions_unique_active 
        ON predictions (status) 
        WHERE status = 'active'
    """)
    op.execute("""
        CREATE UNIQUE INDEX ix_predictions_unique_scheduled 
        ON predictions (status) 
        WHERE status = 'scheduled'
    """)

    # Create user_prediction_choices table
    op.create_table(
        'user_prediction_choices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('prediction_id', sa.Integer(), sa.ForeignKey('predictions.id'), nullable=False),
        sa.Column('selected_button', sa.Integer(), nullable=False),
        sa.Column('selected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('is_test', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id', 'year', 'month', name='uq_user_prediction_choice_per_month')
    )
    op.create_index('ix_user_prediction_choices_telegram_user_id', 'user_prediction_choices', ['telegram_user_id'])


def downgrade() -> None:
    op.drop_table('user_prediction_choices')
    op.drop_index('ix_predictions_unique_scheduled', table_name='predictions')
    op.drop_index('ix_predictions_unique_active', table_name='predictions')
    op.drop_table('predictions')
    op.drop_index('ix_users_telegram_user_id', table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS predictionstatus')
    op.execute('DROP TYPE IF EXISTS mediatype')
