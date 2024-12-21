"""edit_stamp

Revision ID: b23d87c6f6eb
Revises: 8bdca47ef321
Create Date: 2024-12-21 16:41:29.336311

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b23d87c6f6eb'
down_revision: Union[str, None] = '8bdca47ef321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('examination', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    op.add_column('examination_score', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    op.add_column('municipality', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    op.add_column('place', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    op.add_column('region', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    op.add_column('school', sa.Column('edit_stmap', sa.String(length=60), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('school', 'edit_stmap')
    op.drop_column('region', 'edit_stmap')
    op.drop_column('place', 'edit_stmap')
    op.drop_column('municipality', 'edit_stmap')
    op.drop_column('examination_score', 'edit_stmap')
    op.drop_column('examination', 'edit_stmap')
    # ### end Alembic commands ###
