"""rename wellness checkin columns

Revision ID: e5797f5fc47e
Revises: 
Create Date: 2026-09-07 02:09:34.481806
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5797f5fc47e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('wellness_checkins', schema=None) as batch_op:
        batch_op.alter_column('workload_perception', new_column_name='workload_score')
        batch_op.alter_column('wellbeing', new_column_name='wellbeing_score')
        batch_op.alter_column('recovery', new_column_name='recovery_score')


def downgrade() -> None:
    with op.batch_alter_table('wellness_checkins', schema=None) as batch_op:
        batch_op.alter_column('workload_score', new_column_name='workload_perception')
        batch_op.alter_column('wellbeing_score', new_column_name='wellbeing')
        batch_op.alter_column('recovery_score', new_column_name='recovery')
