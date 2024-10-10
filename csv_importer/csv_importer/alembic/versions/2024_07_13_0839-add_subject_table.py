"""add subject table

Revision ID: 2e6adb22a9e7
Revises: 200d6e6d7372
Create Date: 2024-07-13 08:39:54.754031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2e6adb22a9e7'
down_revision: Union[str, None] = '200d6e6d7372'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subject',
    sa.Column('id', sa.String(length=10), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('abbreviations', sa.String(length=30), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('examination_score', 'score',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(),
               existing_nullable=True)
    op.alter_column('examination_score', 'max_possible_score',
               existing_type=postgresql.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('examination_score', 'max_possible_score',
               existing_type=sa.Numeric(),
               type_=postgresql.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('examination_score', 'score',
               existing_type=sa.Numeric(),
               type_=postgresql.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.drop_table('subject')
    # ### end Alembic commands ###