from enum import Enum
from sqlalchemy import insert, select, func, Column, update
from sqlalchemy.orm import Session


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


def _get_max_value(session: Session, int_column: Column) -> int:
    cur = session.execute(
        func.max(int_column)
    )
    first_row = cur.first()
    if first_row and first_row[0]:
        return first_row[0]
    else:
        return 0


def insert_region(session: Session, wd: str, region: str) -> int:
    first = session.execute(
        select(Region.c.id, Region.c.name).where(
            Region.c.wd == wd
        )
    ).first()

    if first and first[0]:
        if first[1] == region:
            logger.verbose_info('Found region: "%s"', first)
        else:
            if not is_dry_run():
                session.execute(
                    update(Region)
                    .where(Region.c.wd == wd)
                    .values({Region.c.name: region})
                )
            logger.verbose_info('Update regionn name for (%d, "%s") from "%s" to "%s"', first[0], wd, first[1], region)

        return first[0]

    id_max = _get_max_value(session, Region.c.id)

    id = id_max + 1
    if not is_dry_run():
        session.execute(
            insert(Region)
            .values({
                Region.c.id: id,
                Region.c.wd: wd,
                Region.c.name: region
            })
        )
    logger.verbose_info('Inserted region (%d, "%s", "%s")', id, wd, region)

    return id


def insert_mun(session: Session, region_id: int, mun: str) -> int:
    first = session.execute(
        select(Municipality.c.id).where(
            Municipality.c.region_id == region_id,
            Municipality.c.name == mun
        )
    ).first()
    if first and first[0]:
        logger.verbose_info('Found municipality "%s" with id %d', mun, first[0])
        return first[0]

    id_max = _get_max_value(session, Municipality.c.id)
    id = id_max + 1

    if not is_dry_run():
        session.execute(
            insert(Municipality)
            .values({
                'id': id,
                'region_id': region_id,
                'name': mun
            })
        )
    logger.verbose_info('Inserted municipality "%s" with id %d', mun, id)

    return id


def insert_mun(session: Session, region_wd: str, wd: str, mun: str) -> int:
    first = session.execute(
        select(Municipality.c.id, Municipality.c.name).where(
            Municipality.c.region_wd == region_wd,
            Municipality.c.wd == wd
        )
    ).first()

    if first and first[0]:
        if first[1] == mun:
            logger.verbose_info('Found municipality (%d, "%s", "%s", "%s")', first[0], region_wd, wd, mun)
        else:
            if not is_dry_run():
                session.execute(
                    update(Municipality)
                    .where(Municipality.c.md == wd)
                    .values({Municipality.c.name: mun})
                )
            logger.verbose_info('Update municipality for (%d, "%s") from "%s" to "%s"', first[0], region_wd, first[1], mun)

        return first[0]

    id_max = _get_max_value(session, Municipality.c.id)
    id = id_max + 1

    region_row = session.execute(select(Region.c.id).where(Region.c.wd == region_wd)).first()

    if not is_dry_run():
        session.execute(
            insert(Municipality)
            .values({
                Municipality.c.id: id,
                Municipality.c.region_id: region_row[0],
                Municipality.c.region_wd: region_wd,
                Municipality.c.wd: wd,
                Municipality.c.name: mun
            })
        )
    logger.verbose_info('Inserted municipality (id=%d, region_id=%d, region_wd="%s", wd="%s", name="%s")', id, region_row[0], region_wd, wd, mun)

    return id


def insert_place(session: Session, mun_id: int, place: str) -> int:
    first = session.execute(
        select(Place.c.id).where(
            Place.c.municipality_id == mun_id,
            Place.c.name == place
        )
    ).first()
    if first and first[0]:
        logger.verbose_info('Found place "%s" with id %d', place, first[0])
        return first[0]

    id_max = _get_max_value(session, Place.c.id)
    id = id_max + 1

    if not is_dry_run():
        session.execute(
            insert(Place)
            .values({
                'id': id,
                'municipality_id': mun_id,
                'name': place
            })
        )
    logger.verbose_info('Inserted place "%s" with id %d', place, id)

    return id


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
