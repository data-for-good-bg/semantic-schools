import os

from collections import defaultdict

from sqlalchemy.engine import Engine

from sqlalchemy.orm import Session

import pandas as pd

from .db import get_db_engine
from .db_actions import (
    insert_examination, insert_or_update_score, insert_mun, insert_place,
    insert_region, insert_school, ImportAction
)
from .runtime import getLogger
from .refine_csv import (
    load_csv, refine_csv_column_names, refine_data,
    extract_school_data, extract_scores_data
)


logger = getLogger(__name__)


REGION  = 'region'
MUN = 'municipality'
PLACE = 'place'


def _import_schools(db: Engine, schools: pd.DataFrame) -> None:
    """
    Imports information about schools, places (cities and villeges),
    municipalities and regions.
    """

    schools = schools.sort_values(by=[REGION, MUN, PLACE])

    with Session(db) as session:
        for i in schools.index:
            school = schools.loc[i]
            region_id = insert_region(session, school[REGION])
            mun_id = insert_mun(session, region_id, school[MUN])
            place_id = insert_place(session, mun_id, school[PLACE])
            insert_school(session, place_id, school['school_admin_id'], school['school'])

        session.commit()


def _import_scores(db: Engine, examination_type: str, year: int, grade: int, scores: pd.DataFrame) -> dict[ImportAction, int]:
    """
    Imports information for examination and all examination scores.
    """
    ops_count = defaultdict(int)
    with Session(db) as session:
        exam_id = insert_examination(session, examination_type, year, grade)
        for i in scores.index:
            score = scores.loc[i]
            subject = score['subject']

            r = insert_or_update_score(
                session,
                exam_id,
                score['school_admin_id'],
                subject,
                int(score['people']),
                float(score['score']),
                float(score['max_possible_score']),
            )
            ops_count[r] += 1

        session.commit()

    return ops_count


def _validate_args(csv_file: str, examination_type: str, grade: int, year: int):
    if not os.path.exists(csv_file):
        raise ValueError(f'Filepath {csv_file} does not exist.')

    if examination_type not in ['dzi', 'nvo']:
        raise ValueError((
            f'Unsupported examination type: {examination_type}. '
            'Supported types are: nvo, dzi'
        ))

    if examination_type == 'nvo':
        supported_grades = [4, 7, 10]
    else:
        supported_grades = [12]

    if grade not in supported_grades:
        raise ValueError((
            f'The specified grade {grade} does not belong to the supported '
            f'grades for examination type {examination_type}: {supported_grades}'
        ))


def import_file(csv_file: str, examination_type: str, grade: int, year: int):
    """
    Imports CSV file containing NVO or DZI data.

    This functionn is used applications - CLI or DAGs.
    """

    _validate_args(csv_file, examination_type, grade, year)

    logger.info('Importing file %s', csv_file)
    raw_data = load_csv(csv_file)
    raw_data = refine_csv_column_names(raw_data)

    refined_data = refine_data(raw_data)
    logger.info('CSV file successfully loaded')

    schools_data = extract_school_data(refined_data)
    logger.info('Successfully extracted school data.')

    scores_data = extract_scores_data(refined_data)
    logger.info('Successfully extracted scores data.')

    db = get_db_engine()

    _import_schools(db, schools_data)

    scores_ops_count = _import_scores(db, examination_type, year, grade, scores_data)

    logger.info('Summary of what has been done with examination_score table: %s', scores_ops_count)
