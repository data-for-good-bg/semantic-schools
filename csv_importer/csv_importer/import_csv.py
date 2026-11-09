import os

from decimal import Decimal
from collections import defaultdict

from sqlalchemy.engine import Engine


from sqlalchemy.orm import Session
from sqlalchemy import select, func

import pandas as pd

from .db import get_db_engine
from .db_actions import (
    insert_examination, insert_or_update_score, check_school_exists,
    insert_school, insert_place, ImportAction
)
from .db_manage import load_subject_abbr_map
from .runtime import getLogger
from .refine_csv import (
    load_csv, refine_csv_column_names, refine_data,
    extract_school_data, extract_scores_data,
    load_json_to_dataframe, extract_scores_dataframe,
    expand_subject_column_in_score_dataframe
)

from .db_models import Place, Municipality, Region
from .models import FOREIGN_COUNTRY


logger = getLogger(__name__)


SUPPORTED_IMPORT_CSV_TYPES = ('schools', 'scores')


REGION  = 'region'
MUN = 'municipality'
PLACE = 'place'


def try_find_place(session: Session, place_name: str, mun: str, region: str) -> str:
    # Here we have some hardcoded standardizing actions for regions and municipalities.

    if region.lower() == 'софия-град':
        region = 'София Столица'
    if region.lower() == 'софия-област':
        region = 'София'

    if mun.lower() == 'столична':
        mun = 'Столична община'
    if mun.lower() == 'гр.добрич':
        mun = 'Добрич'

    if place_name.startswith('с.'):
        place_name = place_name.replace('с.', '').strip()

    if place_name.startswith('гр.'):
        place_name = place_name.replace('гр.', '').strip()

    if place_name == 'Карапелит' and mun == 'Добрич':
        mun = 'Добрич-селска'

    stmt = (
        select(Place.c.id, Place.c.type, Municipality.c.id, Region.c.id).
        select_from(
            Place
            .join(Municipality, Place.c.municipality_id == Municipality.c.id)
            .join(Region, Municipality.c.region_id == Region.c.id)
        ).where(
            func.lower(Place.c.name) == place_name.lower(),
            func.lower(Region.c.name) == region.lower(),
            func.lower(Municipality.c.name) == mun.lower()
        )
    )

    first = session.execute(stmt).first()
    if first and first[0]:
        logger.verbose_info('Found place: (%s, %s, %s, %s) with id %s', first[1], place_name, mun, region, first[0])
        return first[0]
    else:
        logger.verbose_info('Did not find place: (%s, %s, %s)', place_name, mun, region)
        return None


def _import_schools(db: Engine, schools: pd.DataFrame) -> dict[ImportAction, int]:
    """
    Imports information for schools. The assumption is that most of the
    schools are already in the database, because they are imported from
    wikidata. The goal of this function is to import those schools which
    are not in wikidata.

    The function also handles another special case - bulgarian schools in
    foreign countries. For them it will insert a city (place) "Чужбина".

    The function matches schools only by their school_id, the administrative
    number of the school which consists of 6 or 7 digits.

    If a certain shool_id is found in the database it is assumed that the
    school described in the data frame fully matches the school in the database.
    This means that no additional comparisons are made - the school names are
    not compared, nor are the place, municipality and region.
    """

    schools = schools.sort_values(by=[REGION, MUN, PLACE])
    ops_counts = defaultdict(int)

    with Session(db) as session:
        for i in schools.index:
            school = schools.loc[i]

            id = school['school_admin_id']
            school_exists = check_school_exists(session, id)
            if school_exists:
                logger.verbose_info('Found school: %s', id)
                ops_counts[ImportAction.AlreadyExists] += 1
            else:
                school_tuple = (id, school['school'], school[REGION], school[MUN], school[PLACE])
                logger.warning('School does not exist: %s', school_tuple)
                place_id = try_find_place(session, school[PLACE], school[MUN], school[REGION])
                if not place_id and FOREIGN_COUNTRY == school[MUN] == school[REGION]:
                    place_id = insert_place(session, school[PLACE], 'град', FOREIGN_COUNTRY, FOREIGN_COUNTRY)
                if place_id:
                    r = insert_school(session, place_id, school['school_admin_id'], school['school'])
                    ops_counts[r] += 1
                else:
                    logger.error('Cannot find in the database the place for school: %s', school_tuple)
                    ops_counts[ImportAction.Failed] += 1

    return ops_counts


def _import_scores(db: Engine, examination_type: str, year: int, month: str, grade: int, scores: pd.DataFrame) -> dict[ImportAction, int]:
    """
    Imports information for examination and all examination scores.
    """

    ops_count = defaultdict(int)
    with Session(db) as session:
        first_score = scores.loc[0]
        exam_id, _ = insert_examination(session, examination_type, year, month, grade)

        for i in scores.index:
            score = scores.loc[i]
            subject = score['subject']

            r = insert_or_update_score(
                session=session,
                examination_id=exam_id,
                school_id=score['school_admin_id'],
                subject=subject,
                people=int(score['people']),
                score=Decimal(str(score['score'])),
                examination_type=score['examination_type'],
                subject_level=score['level'],
                preparation_type=score['preparation_type'],
                with_validation=bool(score['with_validation']),
            )
            ops_count[r] += 1

    return ops_count


def _validate_args(csv_file: str, examination_type: str, grade: int, month: str):
    if not os.path.exists(csv_file):
        raise ValueError(f'Filepath {csv_file} does not exist.')

    if examination_type not in ['dzi', 'nvo']:
        raise ValueError((
            f'Unsupported examination type: {examination_type}. '
            'Supported types are: nvo, dzi'
        ))

    if examination_type == 'nvo':
        supported_grades = [4, 7, 10]
        supported_month = ['june']
    else:
        supported_grades = [12]
        supported_month = ['june', 'september']

    if grade not in supported_grades:
        raise ValueError((
            f'The specified grade {grade} does not belong to the supported '
            f'grades for examination type {examination_type}: {supported_grades}'
        ))

    if month not in supported_month:
        raise ValueError((
            f'The month {month} is not supported for examination type '
            f'{examination_type}. Supported months are: {supported_month}'
        ))


def import_file(input_file: str, examination_type: str, grade: int, year: int, month: str, to_import=SUPPORTED_IMPORT_CSV_TYPES):
    """
    Imports CSV/JSON file containing NVO or DZI data.

    :param input_file - path to csv or json file
    :param examination_type - it should be `nvo` or `dzi`
    :param grade - the grade of students for which the imported date is about
                   it should be 12 for dzi and 4, 8 or 10 for nvo
    :param year  - the year for which the imported data is about
    :param month  - the month of the year for which the imported data is about
                    TODO: establish convention
    :param to_import - for development/testing purposes - one can select
                       which subset of data to be imported


    """

    _validate_args(input_file, examination_type, grade, month)

    logger.info('Importing file %s', input_file)

    if input_file.endswith('.csv'):
        raw_data = load_csv(input_file)
        raw_data = refine_csv_column_names(raw_data)

        subject_mapping = load_subject_abbr_map()
        refined_data = refine_data(raw_data, subject_mapping)
        logger.info('CSV file successfully loaded')

        schools_data = extract_school_data(refined_data)
        logger.info('Successfully extracted school data.')

        scores_data = extract_scores_data(refined_data)
        logger.info('Successfully extracted scores data.')
    else:
        raw_data = load_json_to_dataframe(input_file)
        scores_data = extract_scores_dataframe(raw_data)
        # scores_data.write_csv(input_file + '.scores_data.csv')
        scores_data = expand_subject_column_in_score_dataframe(scores_data)
        # scores_data.write_csv(input_file + '.subject_expanded.csv')
        scores_data = scores_data.to_pandas()


    db = get_db_engine()

    # if 'schools' in to_import:
    #     schools_ops_count = _import_schools(db, schools_data)
    #     logger.info('Operations over school: %s', schools_ops_count)

    if 'scores' in to_import:
        scores_ops_count = _import_scores(db, examination_type, year, month, grade, scores_data)
        logger.info('Operations over examination_score: %s', scores_ops_count)
