"""
In this file are added functions DB management functions.
"""

from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from collections import OrderedDict, defaultdict

from .models import SubjectItem, get_default_subjects, FOREIGN_COUNTRY
from .db import get_db_engine
from .db_actions import insert_or_update_object
from .db_models import Examination, ExaminationScore, Subject, Region, Municipality
from .runtime import is_dry_run, getLogger


logger = getLogger(__name__)


def load_subject_abbr_map() -> dict[str, SubjectItem]:
    """
    Returns a mapping where the keys are subject abbreviations and the
    values are SubjectItem instances. Since one subject could have multiple
    abbreviations, the same SubjectItem could participate in multiple paris
    in the result dictionary.

    The abbreviations (the keys) are lowercased.

    Check the SubjectItem docs for more details.
    """
    db = get_db_engine()
    with Session(db) as session:
        records = session.execute(select(Subject))
        subject_items = []
        for r in records:
            abbreviations = [] if not r[2] else r[2].split(',')
            subject_items.append(SubjectItem(
                id=r[0], name=r[1], abbreviations=abbreviations
            ))

        result = {}
        for item in subject_items:
            for raw_str in item.raw_strings():
                result[raw_str] = item

        return result


def init_db():
    """
    Initializes a new Database.
    Currently it fills the Subject table.
    TODO: This could be implemented as an alembic migration.
    """

    db = get_db_engine()

    with Session(db) as session:
        _init_subects(session)
        _init_region_and_municipality(session)
        session.commit()


def _init_subects(session: Session):
    default_subject_items = get_default_subjects()
    ops_counts = defaultdict(int)
    for subject_item in default_subject_items:
        abbreviations = ','.join(subject_item.abbreviations)
        r = insert_or_update_object(session, Subject, Subject.c.id, OrderedDict([
            (Subject.c.id, subject_item.id),
            (Subject.c.name, subject_item.name),
            (Subject.c.abbreviations, abbreviations)
        ]))
        ops_counts[r] += 1

    logger.info('Operations over Subject: %s', ops_counts)


def _init_region_and_municipality(session: Session):
    insert_or_update_object(session, Region, Region.c.id, OrderedDict([
        (Region.c.id, FOREIGN_COUNTRY),
        (Region.c.name, FOREIGN_COUNTRY)
    ]))

    insert_or_update_object(session, Municipality, Municipality.c.id, OrderedDict([
        (Municipality.c.id, FOREIGN_COUNTRY),
        (Municipality.c.name, FOREIGN_COUNTRY),
        (Municipality.c.region_id, FOREIGN_COUNTRY)
    ]))


def list_examinations():
    """
    Prints a CSV representation of the Examinations table.
    """
    db = get_db_engine()

    with Session(db) as session:
        records = session.execute(select(Examination))
        col_names = ','.join([f'{c}' for c in Examination.columns])
        print(col_names)
        for r in records:
            print(','.join([f'{v}' for v in r]))

        session.commit()


def delete_examination(examination_id: str):
    """
    Deletes all records from examination_score and examination table with
    the specified examination id.
    """

    db = get_db_engine()

    with Session(db) as session:
        if not is_dry_run():
            session.execute(
                delete(ExaminationScore).
                where(ExaminationScore.c.examination_id == examination_id)
            )
        logger.info('Deleted all examination scores for examination %s', examination_id)

        if not is_dry_run():
            session.execute(
                delete(Examination).
                where(Examination.c.id == examination_id)
            )
        logger.info('Deleted all examination %s', examination_id)

        session.commit()
