from enum import Enum
from sqlalchemy import insert, select, update, Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from collections import OrderedDict
from typing import Any

from .db_models import Subject, Place, School, Examination, ExaminationScore, EDIT_STAMP
from .runtime import getLogger, is_dry_run, edit_stamp


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
    edit_stamp_col = None
    if EDIT_STAMP in model.columns:
        edit_stamp_col = model.columns[EDIT_STAMP]

    input_tuple = tuple(values.values())

    if not isinstance(id_col, list):
        id_col = [id_col]

    where_filters = [
        col == values[col]
        for col in id_col
    ]

    first = session.execute(
        select(values.keys()).
        where(*where_filters)
    ).first()

    try:
        if first:
            if first == input_tuple:
                logger.verbose_info('Found %s: %s', model.name, first)
                return ImportAction.AlreadyExists
            else:
                if not is_dry_run():
                    values_for_update = values.copy()
                    for col in id_col:
                        values_for_update.pop(col)

                    if edit_stamp_col is not None:
                        values_for_update[edit_stamp_col] = edit_stamp()

                    session.execute(
                        update(model)
                        .where(*where_filters)
                        .values(values_for_update)
                    )
                    session.commit()

                logger.verbose_info('Updated %s from %s to %s', model.name, first, input_tuple)
                return ImportAction.Update
        else:
            if not is_dry_run():
                values_for_update = values

                if edit_stamp_col is not None:
                    values_for_update = values.copy()
                    values_for_update[edit_stamp_col] = edit_stamp()

                session.execute(
                    insert(model)
                    .values(values_for_update)
                )
                session.commit()

            logger.verbose_info('Inserted %s %s', model.name, input_tuple)
            return ImportAction.Insert
    except IntegrityError as e:
        logger.error('Failed to process %s item %s because %s', model.name, input_tuple, e)
        session.rollback()
        return ImportAction.Failed


def insert_place(session: Session, place_name: str, place_type: str, mun_id: str, region_id: str) -> str:
    place_id = f'{region_id}-{mun_id}-{place_type}-{place_name}'

    insert_or_update_object(session, Place, Place.c.id, OrderedDict([
        (Place.c.id, place_id),
        (Place.c.municipality_id, mun_id),
        (Place.c.name, place_name),
        (Place.c.type, place_type)
    ]))

    return place_id


def check_school_exists(session: Session, school_id: str) -> bool:
    first = session.execute(
        select(School.c.id).where(School.c.id == school_id)
    ).first()

    return first and first[0]


def insert_school(session: Session, place_id: int, school_id: str, school_name: str) -> ImportAction:
    if not is_dry_run():
        try:
            values = {
                'id': school_id,
                'name': school_name,
                'place_id': place_id
            }
            session.execute(
                insert(School)
                .values(values)
            )
            session.commit()

            logger.verbose_info('Inserted school %s', values)
            return ImportAction.Insert
        except IntegrityError as e:
            logger.error('Failed to insert school %s because %s', values, e)
            session.rollback()
            return ImportAction.Failed


def insert_examination(session: Session, examination_type: str, year: int, grade: int, max_possible_score: float) -> tuple[str, ImportAction]:
    id = f'{examination_type}-{grade}-{year}'
    # a bit hacky way to translate, works only for two types
    translated_type = 'НВО' if examination_type == 'nvo' else 'ДЗИ'


    action = insert_or_update_object(session, Examination, Examination.c.id, OrderedDict([
        (Examination.c.id, id),
        (Examination.c.type, translated_type),
        (Examination.c.year, year),
        (Examination.c.grade_level, grade),
        (Examination.c.max_possible_score, max_possible_score)
    ]))

    return id, action


def insert_or_update_score(session: Session, examination_id: str, school_id: str, subject: str, people: int, score: float) -> ImportAction:

    values = OrderedDict([
        (ExaminationScore.c.examination_id, examination_id),
        (ExaminationScore.c.school_id, school_id),
        (ExaminationScore.c.subject, subject),
        (ExaminationScore.c.people, people),
        (ExaminationScore.c.score, score),
    ])
    id_cols = [ExaminationScore.c.examination_id, ExaminationScore.c.school_id, ExaminationScore.c.subject]

    return insert_or_update_object(
        session, ExaminationScore, id_cols, values
    )
