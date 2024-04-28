#!/usr/bin/env python3

import sys
import os
import logging

from refine_csv import (
    load_csv, refine_csv_column_names, refine_data,
    extract_school_data, extract_scores_data
)
from models import Region, Municipality, Place, School
from sqlalchemy import create_engine, Engine, insert, select, func, Column
from sqlalchemy.orm import Session

import pandas as pd


REGION  = 'region'
MUN = 'municipality'
PLACE = 'place'

logger = logging.getLogger(__name__)


def get_prety_place(value: str) -> str:
    """
    Formats cities and villages in standard way.
    """
    if '.' in value:
        prefix, name = value.split('.')
        return f'{prefix.lower()}. {name.title()}'
    else:
        return value.title()


def get_max_value(session: Session, int_column: Column) -> int:
    cur = session.execute(
        func.max(int_column)
    )
    first_row = cur.first()
    if first_row and first_row[0]:
        return first_row[0]
    else:
        return 0


def insert_region(session: Session, region: str) -> int:
    first = session.execute(
        select(Region.c.id).where(
            Region.c.name == region
        )
    ).first()

    if first and first[0]:
        logger.debug('Found region "%s" with id %d', region, first[0])
        return first[0]

    # TODO: sqlite specific
    id_max = get_max_value(session, Region.c.id)

    id = id_max + 1
    session.execute(
        insert(Region)
        .values({
            'id': id,
            'name': region
        })
    )
    logger.debug('Inserted region "%s" with id %d', region, id)

    return id


def insert_mun(session: Session, region_id: int, mun: str) -> int:
    first = session.execute(
        select(Municipality.c.id).where(
            Municipality.c.region_id == region_id,
            Municipality.c.name == mun
        )
    ).first()
    if first and first[0]:
        logger.debug('Found municipality "%s" with id %d', mun, first[0])
        return first[0]

    id_max = get_max_value(session, Municipality.c.id)
    id = id_max + 1

    session.execute(
        insert(Municipality)
        .values({
            'id': id,
            'region_id': region_id,
            'name': mun
        })
    )
    logger.debug('Inserted municipality "%s" with id %d', mun, id)

    return id


def insert_mun(session: Session, region_id: int, mun: str) -> int:
    first = session.execute(
        select(Municipality.c.id).where(
            Municipality.c.region_id == region_id,
            Municipality.c.name == mun
        )
    ).first()
    if first and first[0]:
        logger.debug('Found municipality "%s" with id %d', mun, first[0])
        return first[0]

    id_max = get_max_value(session, Municipality.c.id)
    id = id_max + 1

    session.execute(
        insert(Municipality)
        .values({
            'id': id,
            'region_id': region_id,
            'name': mun
        })
    )
    logger.debug('Inserted municipality "%s" with id %d', mun, id)

    return id


def insert_place(session: Session, mun_id: int, place: str) -> int:
    first = session.execute(
        select(Place.c.id).where(
            Place.c.municipality_id == mun_id,
            Place.c.name == place
        )
    ).first()
    if first and first[0]:
        logger.debug('Found place "%s" with id %d', place, first[0])
        return first[0]

    id_max = get_max_value(session, Place.c.id)
    id = id_max + 1

    session.execute(
        insert(Place)
        .values({
            'id': id,
            'municipality_id': mun_id,
            'name': place
        })
    )
    logger.debug('Inserted place "%s" with id %d', place, id)

    return id


def insert_school(session: Session, place_id: int, school_id: str, school_name: str) -> None:
    first = session.execute(
        select(School.c.id).where(School.c.id == school_id)
    ).first()
    if first and first[0]:
        logger.debug('Found school "%s" with id %s', school_name, school_id)
        return

    session.execute(
        insert(School)
        .values({
            'id': school_id,
            'name': school_name,
            'place_id': place_id
        })
    )
    logger.debug('Inserted school "%s" with id %s', school_name, school_id)


def import_schools(db: Engine, schools: pd.DataFrame) -> None:

    # format in standard way several columns
    schools[REGION] = schools[REGION].str.title()
    schools[MUN] = schools[MUN].str.title()
    schools[PLACE] = schools[PLACE].apply(get_prety_place)

    schools = schools.sort_values(by=[REGION, MUN, PLACE])

    with Session(db) as session:
        for i in range(len(schools)):
            school = schools.loc[i]
            region_id = insert_region(session, school[REGION])
            mun_id = insert_mun(session, region_id, school[MUN])
            place_id = insert_place(session, mun_id, school[PLACE])
            insert_school(session, place_id, school['school_admin_id'], school['school'])

        session.commit()



def main():

    csv_file = sys.argv[1]

    logger.info('Importing file %s', csv_file)
    raw_data = load_csv(csv_file)
    raw_data = refine_csv_column_names(raw_data)

    refined_data = refine_data(raw_data)
    logger.info('CSV file successfully loaded')

    schools_data = extract_school_data(refined_data)
    logger.info('Successfully extracted school data.')

    scores_data = extract_scores_data(refined_data)
    logger.info('Successfully extracted scores data.')

    db_path = os.path.join(os.path.dirname(__file__), 'sqlite', 'data.db')
    db_url = f'sqlite:///{db_path}'
    db = create_engine(db_url)

    import_schools(db, schools_data)

if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
