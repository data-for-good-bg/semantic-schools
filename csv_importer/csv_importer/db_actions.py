from enum import Enum
from sqlalchemy import insert, select, update, Table
from sqlalchemy.orm import Session
from collections import OrderedDict
from typing import Any

from .models import Subject, Region, Municipality, Place, School, Examination, ExaminationScore
from .runtime import getLogger, is_dry_run


logger = getLogger(__name__)


class ImportAction(Enum):
    """
    It is used as result of some of the methods below. It could be used
    for providing summary of inserted, updated or alredy exissting records
    during execution of CLI app or DAG.
    """
    AlreadyExists = 0
    Insert = 1
    Update = 2
    Failed = 3


def insert_or_update_subject(session: Session, id: str, name: str, abbr: list[str]):
    abbreviations = ','.join(abbr)

    existing_object = session.execute(
        select(Subject.c.name, Subject.c.abbreviations).where(Subject.c.id == id)
    ).first()

    if existing_object:
        if existing_object[0] == name and existing_object[1] == abbreviations:
            logger.verbose_info('Subject %s already exist', id)
        else:
            if not is_dry_run():
                session.execute(
                    update(Subject)
                    .where(Subject.c.id == id)
                    .values({
                        Subject.c.name.name: name,
                        Subject.c.abbreviations.name: abbreviations
                    })
                )
            logger.verbose_info('Updated subject %s, %s, %s', id, name, abbreviations)
    else:
        if not is_dry_run():
            session.execute(
                insert(Subject)
                .values({
                    Subject.c.id.name: id,
                    Subject.c.name.name: name,
                    Subject.c.abbreviations.name: abbreviations
                })
            )
        logger.verbose_info('Inserted subject %s, %s, %s', id, name, abbreviations)


def insert_or_update_object(session: Session, model: Table, id_col: Any, values: OrderedDict) -> ImportAction:
    input_tuple = tuple(values.values())

    first = session.execute(
        select(values.keys()).
        where(id_col == values[id_col])
    ).first()

    if first:
        if first == input_tuple:
            logger.verbose_info('Found %s: %s', model.name, first)
            return ImportAction.AlreadyExists
        else:
            if not is_dry_run():
                values_for_update = values.copy()
                values_for_update.pop(id_col)
                session.execute(
                    update(model)
                    .where(id_col == values[id_col])
                    .values(values_for_update)
                )
            logger.verbose_info('Updated %s from %s to %s', model.name, first, input_tuple)
            return ImportAction.Update
    else:
        if not is_dry_run():
            session.execute(
                insert(model)
                .values(values)
            )
        logger.verbose_info('Inserted %s %s', model.name, input_tuple)
        return ImportAction.Insert


def insert_region(session: Session, id: str, name: str, area_id: str, longitude: str, latitude: str):
    # TODO: delete when all the code is not using this
    pass


def insert_mun(session: Session, id: str, region_id: str, name: str, area_id: str, longitude: str, latitude: str) -> str:
    # TODO: delete when all the code is not using this
    pass


def insert_place():
    # TODO: delete when all the code is not using this
    pass


def insert_school(session: Session, place_id: int, school_id: str, school_name: str) -> None:
    first = session.execute(
        select(School.c.id).where(School.c.id == school_id)
    ).first()
    if first and first[0]:
        logger.verbose_info('Found school with id %s', school_id)
        return

    if not is_dry_run():
        session.execute(
            insert(School)
            .values({
                'id': school_id,
                'name': school_name,
                'place_id': place_id
            })
        )
    logger.verbose_info('Inserted school "%s" with id %s', school_name, school_id)


def insert_examination(session: Session, examination_type: str, year: int, grade: int) -> str:
    id = f'{examination_type}-{grade}-{year}'
    first = session.execute(
        select(Examination.c.id).where(Examination.c.id == id)
    ).first()
    if first and first[0]:
        logger.verbose_info('Examination with id %s already exists.', id)
        return id

    # a bit hacky way to translate, works only for two types
    translated_type = 'НВО' if examination_type == 'nvo' else 'ДЗИ'

    if not is_dry_run():
        session.execute(
            insert(Examination).values({
                'id': id,
                'type': translated_type,
                'year': year,
                'grade_level': grade
            })
        )

    logger.verbose_info('Inserted Examination with id %s.', id)
    return id


def insert_or_update_score(session: Session, examination_id: str, school_id: str, subject: str, people: int, score: float, max_possible_score: float) -> ImportAction:
    first = session.execute(
        select(ExaminationScore.c.score, ExaminationScore.c.people, ExaminationScore.c.max_possible_score)
        .where(ExaminationScore.c.examination_id == examination_id,
               ExaminationScore.c.school_id == school_id,
               ExaminationScore.c.subject == subject)
    ).first()
    if first:
        if float(first[0]) != score or first[1] != people or float(first[2]) != max_possible_score:
            if not is_dry_run():
                session.execute(
                    update(ExaminationScore)
                    .where(ExaminationScore.c.examination_id == examination_id,
                            ExaminationScore.c.school_id == school_id,
                            ExaminationScore.c.subject == subject)
                    .values({
                        'score': score,
                        'people': people,
                        'max_possible_score': max_possible_score
                    })
                )
            logger.verbose_info('Updated examination score %s, %s, %s, %d, %f, %f', examination_id, school_id, subject, people, score, max_possible_score)
            return ImportAction.Update
        else:
            logger.verbose_info('Already existing examination score %s, %s, %s, %d, %f, %f', examination_id, school_id, subject, people, score, max_possible_score)
            return ImportAction.AlreadyExists
    else:
        if not is_dry_run():
            session.execute(
                insert(ExaminationScore)
                .values({
                    'examination_id': examination_id,
                    'school_id': school_id,
                    'subject': subject,
                    'people': people,
                    'score': score,
                    'max_possible_score': max_possible_score
                })
            )
        logger.verbose_info('Inserted examination score %s, %s, %s, %d, %f, %f', examination_id, school_id, subject, people, score, max_possible_score)
        return ImportAction.Insert
