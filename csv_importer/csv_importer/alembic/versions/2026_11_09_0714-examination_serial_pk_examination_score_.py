"""2026 update: examination serial pk and examination_score rework

Revision ID: 964f79162b24
Revises: ff01b33adfe6
Create Date: 2026-11-09 07:14:38.588512

Single migration taking the initial schema to the 2026 one (it merges and
replaces the former '2026 update' revision 29e818b3bdbb):

* adds `month` to `examination` and drops `max_possible_score`
* adds `examination_type`, `subject_level`, `preparation_type` and
  `with_validation` to `examination_score` (all NOT NULL with server
  defaults, so existing rows are backfilled)
* changes the primary key of `examination` from a string id to an
  autoincremented integer (serial), makes
  `examination_score.examination_id` an integer foreign key to it (with
  CASCADE), replaces the compound primary key of `examination_score` with a
  unique index (extended with `with_validation` and `preparation_type`) and
  adds an autoincremented integer `id` primary key to `examination_score`

The migration is written to work on non-empty tables: plain
ALTER COLUMN ... TYPE integer cannot cast the existing varchar ids, so new
integer columns are added, backfilled through the old string ids and then
swapped in place of the old ones.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '964f79162b24'
down_revision: Union[str, None] = 'ff01b33adfe6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # the FKs and the compound PK reference the old string examination_id,
    # drop them first ('examination_score_pkey' is the default PostgreSQL
    # name for the unnamed PK)
    op.drop_constraint('examination_score_examination_id_fkey', 'examination_score', type_='foreignkey')
    op.drop_constraint('examination_score_school_id_fkey', 'examination_score', type_='foreignkey')
    op.drop_constraint('examination_score_pkey', 'examination_score', type_='primary')

    op.add_column('examination', sa.Column('month', sa.String(length=20), nullable=True))
    op.drop_column('examination', 'max_possible_score')

    # server_default backfills the existing rows with the default value when
    # the NOT NULL column is added (PostgreSQL fills existing rows on ADD COLUMN
    # ... DEFAULT); the plain `default=` in db_models.py is Python-side only
    # and never reaches the DDL.
    op.add_column('examination_score', sa.Column('examination_type', sa.String(length=5), nullable=False, server_default=sa.text("'-'")))
    op.add_column('examination_score', sa.Column('subject_level', sa.String(length=10), nullable=False, server_default=sa.text("''")))
    op.add_column('examination_score', sa.Column('preparation_type', sa.String(length=5), nullable=False, server_default=sa.text("'-'")))
    op.add_column('examination_score', sa.Column('with_validation', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # new integer id for examination, backfilled from a sequence so that
    # existing rows get unique values; DEFAULT + OWNED BY make the column
    # behave like a serial for future inserts
    op.execute('CREATE SEQUENCE examination_id_seq')
    op.add_column('examination', sa.Column('new_id', sa.Integer(), nullable=True))
    op.execute('UPDATE examination SET new_id = nextval(\'examination_id_seq\')')
    op.execute('ALTER TABLE examination ALTER COLUMN new_id SET NOT NULL')
    op.execute('ALTER TABLE examination ALTER COLUMN new_id SET DEFAULT nextval(\'examination_id_seq\')')
    op.execute('ALTER SEQUENCE examination_id_seq OWNED BY examination.new_id')

    # new integer examination_id for examination_score, backfilled through a
    # join on the old string ids (both old columns still exist at this point)
    op.add_column('examination_score', sa.Column('new_examination_id', sa.Integer(), nullable=True))
    op.execute(
        'UPDATE examination_score es SET new_examination_id = e.new_id '
        'FROM examination e WHERE es.examination_id = e.id'
    )
    op.execute('ALTER TABLE examination_score ALTER COLUMN new_examination_id SET NOT NULL')

    # swap the new integer id in place of the old string one on examination
    # (must happen before recreating the FK, so that examination.id is
    # already an integer)
    op.drop_constraint('examination_pkey', 'examination', type_='primary')
    op.drop_column('examination', 'id')
    op.alter_column('examination', 'new_id', new_column_name='id')
    op.create_primary_key('examination_pkey', 'examination', ['id'])

    op.drop_column('examination_score', 'examination_id')
    op.alter_column('examination_score', 'new_examination_id', new_column_name='examination_id')
    op.create_foreign_key('examination_score_examination_id_fkey', 'examination_score', 'examination', ['examination_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('examination_score_school_id_fkey', 'examination_score', 'school', ['school_id'], ['id'], ondelete='CASCADE')

    # new autoincremented surrogate primary key for examination_score
    op.execute('CREATE SEQUENCE examination_score_id_seq')
    op.add_column('examination_score', sa.Column('id', sa.Integer(), nullable=True))
    op.execute('UPDATE examination_score SET id = nextval(\'examination_score_id_seq\')')
    op.execute('ALTER TABLE examination_score ALTER COLUMN id SET NOT NULL')
    op.execute('ALTER TABLE examination_score ALTER COLUMN id SET DEFAULT nextval(\'examination_score_id_seq\')')
    op.execute('ALTER SEQUENCE examination_score_id_seq OWNED BY examination_score.id')
    op.create_primary_key('examination_score_pkey', 'examination_score', ['id'])

    # the former compound primary key becomes a unique index, extended with
    # with_validation and preparation_type
    op.create_index('ix_examination_score_unique', 'examination_score', ['examination_id', 'school_id', 'subject', 'examination_type', 'subject_level', 'with_validation', 'preparation_type'], unique=True)


def downgrade() -> None:
    # NB: the original string examination ids (e.g. 'dzi-12-2017') are not
    # recoverable from the integer ones, the downgrade casts the integers
    # back to varchar instead
    op.drop_index('ix_examination_score_unique', table_name='examination_score')
    op.drop_constraint('examination_score_examination_id_fkey', 'examination_score', type_='foreignkey')
    op.drop_constraint('examination_score_school_id_fkey', 'examination_score', type_='foreignkey')
    op.drop_constraint('examination_score_pkey', 'examination_score', type_='primary')
    # drops the sequence owned by the column as well
    op.drop_column('examination_score', 'id')
    op.alter_column('examination_score', 'examination_id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=15),
               existing_nullable=False,
               postgresql_using='examination_id::varchar(15)')

    op.execute('ALTER TABLE examination ALTER COLUMN id DROP DEFAULT')
    op.execute('DROP SEQUENCE examination_id_seq')
    op.drop_constraint('examination_pkey', 'examination', type_='primary')
    op.alter_column('examination', 'id',
               existing_type=sa.Integer(),
               type_=sa.VARCHAR(length=15),
               existing_nullable=False,
               postgresql_using='id::varchar(15)')
    op.create_primary_key('examination_pkey', 'examination', ['id'])

    # restore the original FKs (without CASCADE) and the 3-column PK
    op.create_foreign_key('examination_score_school_id_fkey', 'examination_score', 'school', ['school_id'], ['id'])
    op.create_foreign_key('examination_score_examination_id_fkey', 'examination_score', 'examination', ['examination_id'], ['id'])
    op.create_primary_key('examination_score_pkey', 'examination_score', ['examination_id', 'school_id', 'subject'])

    op.drop_column('examination_score', 'with_validation')
    op.drop_column('examination_score', 'preparation_type')
    op.drop_column('examination_score', 'subject_level')
    op.drop_column('examination_score', 'examination_type')
    op.add_column('examination', sa.Column('max_possible_score', sa.NUMERIC(), autoincrement=False, nullable=True))
    op.drop_column('examination', 'month')
