"""add_school_table_type

Revision ID: c4fb9d774a75
Revises: ff01b33adfe6
Create Date: 2025-02-23 12:35:28.677573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4fb9d774a75'
down_revision: Union[str, None] = 'ff01b33adfe6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('school_type',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('details', sa.String(length=60), nullable=True),
    sa.Column('edit_stamp', sa.String(length=60), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    op.execute(
        "insert into school_type values(1, '-', '-', 'migration_2025_02_23')"
    )

    op.add_column('school', sa.Column('school_type_id', sa.Integer(), nullable=True))

    op.execute(
        'UPDATE school SET school_type_id = 1 WHERE school_type_id IS NULL'
    )

    op.alter_column('school', 'school_type_id',
        existing_type=sa.Integer(),
        nullable=False
    )
    op.create_foreign_key(None, 'school', 'school_type', ['school_type_id'], ['id'])

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'school', type_='foreignkey')
    op.drop_column('school', 'school_type_id')
    op.drop_table('school_type')
    # ### end Alembic commands ###
