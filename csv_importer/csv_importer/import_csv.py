import os

from collections import defaultdict

from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session
from sqlalchemy import select

import pandas as pd

from .db import get_db_engine
from .db_actions import (
    insert_examination, insert_or_update_score, check_school_exists,
    insert_school, insert_place, ImportAction
)
from .runtime import getLogger
from .refine_csv import (
    load_csv, refine_csv_column_names, refine_data,
    extract_school_data, extract_scores_data
)

from .models import Place, Municipality, Region


logger = getLogger(__name__)


REGION  = 'region'
MUN = 'municipality'
PLACE = 'place'


def try_find_place(session: Session, place_name: str, mun: str, region: str) -> str:
    # Here we have some hardcoded cleaning actions,
    # Some of them make sense to be here, but some of them probably can be
    # generalized.
    # TODO:
    # Also in refince_csv there's code which capitlizes only the first letter
    # of the place names, which probably has impact here. Also that code in
    # refine_csv was added after I put some of the "magics" below...

    if region.lower() == 'софия-град':
        region = 'София Столица'
    if region.lower() == 'софия-област':
        region = 'София'

    if mun.lower() == 'столична':
        mun = 'Столична община'
    if mun.lower() == 'гр.добрич':
        mun = 'Добрич'
    if mun == 'Ново Село':
        mun = 'Ново село'
    if mun == 'Бобов Дол':
        mun = 'Бобов дол'
    if mun == 'Сапарева Баня':
        mun = 'Сапарева баня'
    if mun == 'Червен Бряг':
        mun = 'Червен бряг'
    if mun == 'Минерални Бани':
        mun = 'Минерални бани'


    if place_name.startswith('с.'):
        place_type = 'село'
        place_name = place_name.replace('с.', '').strip()
    elif place_name.startswith('гр.'):
        place_type = 'град'
        place_name = place_name.replace('гр.', '').strip()
    else:
        place_type = ''

    if place_name == 'Ново Село':
        place_name = 'Ново село'
    if place_name == 'Бобов Дол':
        place_name = 'Бобов дол'
    if place_name == 'Сапарева Баня':
        place_name = 'Сапарева баня'
    if place_name == 'Червен Бряг':
        place_name = 'Червен бряг'

    if place_name == 'Карапелит' and mun == 'Добрич':
        mun = 'Добрич-селска'

    stmt = (
        select(Place.c.id, Place.c.type, Municipality.c.id, Region.c.id).
        select_from(
            Place
            .join(Municipality, Place.c.municipality_id == Municipality.c.id)
            .join(Region, Municipality.c.region_id == Region.c.id)
        ).where(
            Place.c.name == place_name,
            Region.c.name == region,
            Municipality.c.name == mun
        )
    )

    first = session.execute(stmt).first()
    if first and first[0]:
        logger.verbose_info('Found place: (%s, %s, %s, %s) with id %s', first[1], place_name, mun, region, first[0])
        return first[0]
    else:
        logger.verbose_info('Did not find place: (%s, %s, %s, %s)', place_type, place_name, mun, region)
        return None


def _import_schools(db: Engine, schools: pd.DataFrame) -> None:
    """
    Imports information about schools, places (cities and villeges),
    municipalities and regions.
    """

    schools = schools.sort_values(by=[REGION, MUN, PLACE])

    with Session(db) as session:
        for i in schools.index:
            school = schools.loc[i]

            id = school['school_admin_id']
            school_exists = check_school_exists(session, id)
            if school_exists:
                logger.verbose_info('Found school: %s', id)
            else:
                logger.verbose_info('School does not exist: %s %s %s %s', id, school[REGION], school[MUN], school[PLACE])
                place_id = try_find_place(session, school[PLACE], school[MUN], school[REGION])
                if not place_id and 'Чужбина' == school[MUN] == school[REGION]:
                    place_id = insert_place(session, school[PLACE], 'град', 'Чужбина', 'Чужбина')
                if place_id:
                    insert_school(session, place_id, school['school_admin_id'], school['school'])

        session.commit()


def _import_scores(db: Engine, examination_type: str, year: int, grade: int, scores: pd.DataFrame) -> dict[ImportAction, int]:
    """
    Imports information for examination and all examination scores.
    """
    ops_count = defaultdict(int)
    with Session(db) as session:
        exam_id, _ = insert_examination(session, examination_type, year, grade)
        session.commit()

        for i in scores.index:
            score = scores.loc[i]
            subject = score['subject']

            try:
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
            except IntegrityError as e:
                logger.verbose_info('Failed to process score item %s because %s', score, e)
                session.rollback()
                ops_count[ImportAction.Failed] += 1

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
