"""Add indexes for statistics queries on user_prediction_choices

Revision ID: 002_add_choice_indexes
Revises: 001_initial
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002_add_choice_indexes'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Monthly statistics filter by (year, month) without telegram_user_id, so the
    # existing unique constraint can't help — add a dedicated index.
    op.create_index(
        'ix_choices_year_month',
        'user_prediction_choices',
        ['year', 'month'],
    )
    # Per-prediction statistics filter by prediction_id (FK, previously unindexed).
    op.create_index(
        'ix_choices_prediction_id',
        'user_prediction_choices',
        ['prediction_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_choices_prediction_id', table_name='user_prediction_choices')
    op.drop_index('ix_choices_year_month', table_name='user_prediction_choices')
