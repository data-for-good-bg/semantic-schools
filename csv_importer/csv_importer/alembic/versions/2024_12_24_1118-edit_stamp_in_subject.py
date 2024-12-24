"""edit_stamp in subject

Revision ID: 9f0795f7e3e2
Revises: 4e56f55f89cd
Create Date: 2024-12-24 11:18:42.106702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f0795f7e3e2'
down_revision: Union[str, None] = '4e56f55f89cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('subject', sa.Column('edit_stamp', sa.String(length=60), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subject', 'edit_stamp')
    # ### end Alembic commands ###
