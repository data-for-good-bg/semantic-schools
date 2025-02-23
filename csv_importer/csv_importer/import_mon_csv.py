import pandas as pd

from collections import OrderedDict, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from .runtime import getLogger
from .db import get_db_engine
from .db_actions import insert_or_update_object
from .db_models import SchoolType, SchoolFundingSource


logger = getLogger(__name__)

# Mapping of Bulgarian column names to English
COLUMN_MAP = {
    'код по неиспуо': 'school_id',
    'пълно наименование на институция': 'name',
    'вид на институция': 'institution_type',
    'детайлен вид на институция': 'institution_type_detailed',
    'вид на институцията според финнсирането': 'funding_type',
    'финансира се от': 'funded_by',
    'наименование на адрес на осъществяване на дейността': 'activity_address',
    'тип на сградата': 'building_type',
    'код от кадастъра': 'cadastre_code',
    'географски координати (ширина)': 'latitude',
    'географски координати (дължина)': 'longitude',
    'област': 'region',
    'община': 'municipality',
    'населено място': 'place',
    'адрес': 'address'
}


def _import_school_type(session: Session, raw_data: pd.DataFrame) -> dict[str, int]:
    # Extract unique institution types
    data = raw_data[['institution_type', 'institution_type_detailed']].drop_duplicates().copy()
    logger.verbose_info(f'Found {len(data)} unique institution types')


    counts = defaultdict(int)
    for _, row in data.iterrows():
        result = insert_or_update_object(
            session,
            SchoolType,
            id_col=[SchoolType.c.name, SchoolType.c.details],
            values=OrderedDict([
                (SchoolType.c.name, row['institution_type']),
                (SchoolType.c.details, row['institution_type_detailed'])
            ])
        )
        counts[result] += 1

    logger.info('Imported school types: %s', counts)

    rows = session.execute(
        select(SchoolType.c.id, SchoolType.c.name, SchoolType.c.details)
    ).fetchall()

    logger.verbose_info(f'Found {len(rows)} school types')
    result = {}
    for id, name, details in rows:
        result[f'{name}-{details}'] = id

    return result


def _import_school_funding_source(session: Session, raw_data: pd.DataFrame) -> dict[str, int]:
    # extract unique funding sources
    data = raw_data[['funding_type', 'funded_by']].drop_duplicates()
    logger.verbose_info(f'Found {len(data)} unique funding sources')

    counts = defaultdict(int)
    for _, row in data.iterrows():
        result = insert_or_update_object(
            session,
            SchoolFundingSource,
            id_col=[SchoolFundingSource.c.funding_type, SchoolFundingSource.c.funding_institution_name],
            values=OrderedDict([
                (SchoolFundingSource.c.funding_type, row['funding_type']),
                (SchoolFundingSource.c.funding_institution_name, row['funded_by'])
            ])
        )
        counts[result] += 1

    logger.info('Imported funding sources: %s', counts)

    rows = session.execute(
        select(SchoolFundingSource.c.id, SchoolFundingSource.c.funding_type, SchoolFundingSource.c.funding_institution_name)
    ).fetchall()

    logger.verbose_info(f'Found {len(rows)} school funding sources')
    result = {}
    for id, type, inst_name in rows:
        result[f'{type}-{inst_name}'] = id

    return result


def _import_schools(session: Session, data: pd.DataFrame) -> None:

    for school_id, school_rows in data.groupby('school_id'):
        logger.verbose_info(f'Processing school {school_id} with {len(school_rows)} entries')

        valid_rows = school_rows[
            school_rows['building_type'].ne('')
            & school_rows['building_type'].notna()
        ]

        for _, row in valid_rows.iterrows():
            logger.verbose_info(f'Importing school {school_id} {row["name"]}')
            break
        else:
            logger.info(f'Skipping school {school_id} {school_rows.iloc[0]["name"]}')


def import_mon_csv(csv_file: str) -> None:
    """
    Imports a MON CSV file.
    """
    data = pd.read_csv(csv_file)
    data.columns = data.columns.str.lower()
    data = data.rename(columns=COLUMN_MAP)

    # Trim whitespace from all string columns
    for column in data.select_dtypes(include=['object']).columns:
        data[column] = data[column].str.strip()

    # Filter out kindergartens
    initial_count = len(data)
    data = data[data['institution_type'] != 'детска градина']
    logger.verbose_info(f'Filtered out {initial_count - len(data)} детска градина entries')

    # initial_count = len(data)
    # data = data[data['building_type'] != 'общежитие']
    # logger.verbose_info(f'Filtered out {initial_count - len(data)} общежитие entries')

    # # Drop unnecessary columns and duplicates
    # columns_to_drop = ['activity_address', 'building_type', 'cadastre_code']
    # data.drop(columns=columns_to_drop, inplace=True)



    initial_count = len(data)
    data.drop_duplicates(inplace=True)
    logger.verbose_info(f'Removed {initial_count - len(data)} duplicate entries')

    data.to_csv('/tmp/data.csv', index=False)

    db = get_db_engine()
    with Session(db) as session:
        school_types_map = _import_school_type(session, data)
        session.commit()
        logger.verbose_info(f'School types: {school_types_map}')

        school_funding_sources_map = _import_school_funding_source(session, data)
        session.commit()
        logger.verbose_info(f'School funding sources: {school_funding_sources_map}')

        # Replace type columns with their IDs
        data['school_type_id'] = data.apply(
            lambda row: school_types_map[f"{row['institution_type']}-{row['institution_type_detailed']}"],
            axis=1
        )
        data.drop(['institution_type', 'institution_type_detailed'], axis=1, inplace=True)

        # Replace funding columns with their IDs
        data['school_funding_source_id'] = data.apply(
            lambda row: school_funding_sources_map[f"{row['funding_type']}-{row['funded_by']}"],
            axis=1
        )
        data.drop(['funding_type', 'funded_by'], axis=1, inplace=True)

        logger.verbose_info(f'Replaced type and funding columns with their IDs')

        _import_schools(session, data)
