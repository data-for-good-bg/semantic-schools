#!/usr/bin/env python3

import sys
import os
import logging

from refine_csv import (
    load_csv, refine_csv_column_names, refine_data,
    extract_school_data, extract_scores_data
)
from models import Region, Municipality, Place, School, Examination, ExaminationScore
from sqlalchemy import create_engine, Engine, insert, select, func, Column, update
from sqlalchemy.orm import Session

import pandas as pd


REGION  = 'region'
MUN = 'municipality'
PLACE = 'place'

logger = logging.getLogger(__name__)


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

    schools = schools.sort_values(by=[REGION, MUN, PLACE])

    with Session(db) as session:
        for i in schools.index:
            school = schools.loc[i]
            region_id = insert_region(session, school[REGION])
            mun_id = insert_mun(session, region_id, school[MUN])
            place_id = insert_place(session, mun_id, school[PLACE])
            insert_school(session, place_id, school['school_admin_id'], school['school'])

        session.commit()


def insert_examination(session: Session, examination_type: str, year: int, grade: int) -> str:
    id = f'{examination_type}-{grade}-{year}'
    first = session.execute(
        select(Examination.c.id).where(Examination.c.id == id)
    ).first()
    if first and first[0]:
        logger.debug('Examination with id %s already exists.', id)
        return id

    # a bit hacky way to translate, works only for two types
    translated_type = 'НВО' if examination_type == 'nvo' else 'ДЗИ'

    session.execute(
        insert(Examination).values({
            'id': id,
            'type': translated_type,
            'year': year,
            'grade_level': grade
        })
    )

    logger.debug('Inserted Examination with id %s.', id)
    return id


def insert_score(session: Session, examination_id: str, school_id: str, subject: str, subject_specifier: str, people: int, score: float, max_possible_score: float):
    first = session.execute(
        select(ExaminationScore.c.score, ExaminationScore.c.people, ExaminationScore.c.max_possible_score)
        .where(ExaminationScore.c.examination_id == examination_id,
               ExaminationScore.c.school_id == school_id,
               ExaminationScore.c.subject == subject,
               ExaminationScore.c.subject_specifier == subject_specifier)
    ).first()
    if first:
        if first[0] != score or first[1] != people or first[2] != max_possible_score:
            session.execute(
                update(ExaminationScore)
                .where(ExaminationScore.c.examination_id == examination_id,
                        ExaminationScore.c.school_id == school_id,
                        ExaminationScore.c.subject == subject,
                        ExaminationScore.c.subject_specifier == subject_specifier)
                .values({
                    'score': score,
                    'people': people,
                    'max_possible_score': max_possible_score
                })
            )
            logger.debug('Updated examination score %s %s %s %s %d %f %f', examination_id, school_id, subject, subject_specifier, people, score, max_possible_score)
        else:
            logger.debug('Already existing examination score %s %s %s %s %d %f %f', examination_id, school_id, subject, subject_specifier, people, score, max_possible_score)
    else:
        session.execute(
            insert(ExaminationScore)
            .values({
                'examination_id': examination_id,
                'school_id': school_id,
                'subject': subject,
                'subject_specifier': subject_specifier,
                'people': people,
                'score': score,
                'max_possible_score': max_possible_score
            })
        )
        logger.debug('Inserted examination score %s %s %s %s %d %f %f', examination_id, school_id, subject, subject_specifier, people, score, max_possible_score)


def import_scores(db: Engine, examination_type: str, year: int, grade: int, scores: pd.DataFrame) -> None:
    with Session(db) as session:
        exam_id = insert_examination(session, examination_type, year, grade)
        for i in scores.index:
            score = scores.loc[i]
            subject = score['subject']
            if '-' in subject:
                parts = subject.split('-')
                subject = parts[0]
                subject_specifier = '-'.join(parts[1:])
            else:
                subject_specifier = ''

            insert_score(
                session,
                exam_id,
                score['school_admin_id'],
                subject,
                subject_specifier,
                int(score['people']),
                score['score'],
                score['max_possible_score'],
            )

        session.commit()


def extract_examination_attributes(filename: str):
    filename = os.path.basename(filename)
    parts = filename.lower().split('-')
    examination_type = parts[0]
    if examination_type not in ['nvo', 'dzi']:
        raise ValueError(f'{examination_type} is not supported. Supported examination types are "nvo" and "dzi".')

    if examination_type == 'nvo':
        grade = int(parts[1])
        year = int(parts[2])
    else:
        grade = 12
        year = int(parts[1])

    return examination_type, grade, year


def main():

    csv_file = sys.argv[1]

    examination_type, grade, year = extract_examination_attributes(csv_file)

    logger.info('Importing file %s', csv_file)
    raw_data = load_csv(csv_file)
    raw_data = refine_csv_column_names(raw_data)

    refined_data = refine_data(raw_data)
    logger.info('CSV file successfully loaded')

    schools_data = extract_school_data(refined_data)
    logger.info('Successfully extracted school data.')

    scores_data = extract_scores_data(refined_data)
    logger.info('Successfully extracted scores data.')

    # NB: to work with sqlite uncomment these lines
    # db_path = os.path.join(os.path.dirname(__file__), 'sqlite', 'data.db')
    # db_url = f'sqlite:///{db_path}'

    # NB: to work with postgre use this line
    db_url = f'postgresql://postgres:data-for-good@localhost/eddata'

    db = create_engine(db_url)

    import_schools(db, schools_data)

    import_scores(db, examination_type, year, grade, scores_data)

if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
