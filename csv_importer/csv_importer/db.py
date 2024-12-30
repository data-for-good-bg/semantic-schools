import os

from sqlalchemy import create_engine, text as raw_statement
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


KNOWN_ALEMBIC_VERSION = 'ff01b33adfe6'

DEFAULT_DB_URL = 'postgresql://postgres:data-for-good@localhost/eddata'


def check_db_version(db: Engine):
    with Session(db) as session:
        cursor = session.execute(raw_statement('select version_num from alembic_version;'))
        row = cursor.fetchone()
        actual_version = row[0]

    if actual_version != KNOWN_ALEMBIC_VERSION:
        raise RuntimeError((
            f'The database version is: {actual_version}, while it is '
            f'expected to be {KNOWN_ALEMBIC_VERSION}. '
            'Cannot continue because the data could be corrupted.'
        ))


def get_db_engine() -> Engine:
    """
    Returns initialized SQLAlchemy Engine, also verifies that the database
    is update to the expected alembic (schema) version.

    All DB consumers should use this function to obtain SQLAlchemy engine.
    """

    # example sqlite URL: f'sqlite:///{os.path.join(os.path.dirname(__file__), 'sqlite', 'data.db')}'
    db_url = os.environ.get('DB_URL', DEFAULT_DB_URL)
    db = create_engine(db_url)

    check_db_version(db)

    return db
