"""
In this file are added functions DB management functions.
"""

from dataclasses import dataclass
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


from .db import get_db_engine
from .db_actions import insert_or_update_subject
from .models import Examination, ExaminationScore, Subject
from .runtime import is_dry_run, getLogger


logger = getLogger(__name__)


@dataclass
class SubjectItem:
    """
    This class facilitates working with Subjects and the fact some of the
    have multiple abbraviations.
    The problem: For example Испански Език in different CSV files is found
    with ИЕ and ИспЕ. In the database we want to have just one subject abbreviation

    The `id` attribute is always an abbreviation of the subject, the `name` is
    the full name of the subject. The `abbreviations` is list of all other
    abbreviations known for the subject. This list could be empty.

    The `raw_strings()` method returns list of lowercased all possible
    abbreviations. This list is used to build a dictionary where the keys
    are abbreviations, the values are SubjectItem instances. Such dictionary
    is used in refince_csv for mapping the found subject abbreviation in certain
    CSV to the choosen one.

    In the database there is a table Subject which has the same columnd - id,
    name and abbreviations. This table is used as source of information
    for SubjectItem instances.
    Check the function load_subject_abbr_map() below.

    The foreign languages subjects (English, Spanish, Russion, etc.) have
    variations with different levels - Б1, Б1.1 and Б2. They are treated as
    different subject items, so in the Subject table there are records for
    'АЕ', 'АЕ-Б1', 'АЕ-Б1.1', 'АЕ-Б2', and similar records for all other foreign
    languagues.

    Below in the init_db() function there's is manually initialized list
    of SubjectItems which is used to fill the Subject table in the database.

    """
    id: str
    name: str
    abbreviations: list[str]

    def __post_init__(self):
        self.id = self.id.upper()

    def raw_strings(self):
        result = []
        for a in [self.id, *self.abbreviations]:
            result.append(f'{a.lower()}')
        return result


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
    TODO: This could be implemented as alembic migration.
    """

    language_levels = ['Б1', 'Б1.1', 'Б2']

    def _variations(this: SubjectItem, variations: list[str]) -> list[SubjectItem]:
        result = [this]
        for v in variations:
            result.append(
                SubjectItem(
                    id=f'{this.id}-{v}',
                    name=f'{this.name} {v}',
                abbreviations=[f'{a}-{v}' for a in this.abbreviations]
                )
            )

        return result


    def _lang_variations(this: SubjectItem) -> list[SubjectItem]:
        return _variations(this, language_levels)

    default_subject_items = [
        *_lang_variations(SubjectItem(id='АЕ', abbreviations=[], name='Английски език')),
        SubjectItem(id='БЕЛ', abbreviations=[], name='Български език и литература'),
        SubjectItem(id='БЗО', abbreviations=[], name='Биология и здравно образование'),
        SubjectItem(id='ГЕО', abbreviations=['ГИ'], name='География и икономика'),
        SubjectItem(id='ДИППК', abbreviations=[], name='Държавен изпит за придобиване на професионална квалификация'),
        SubjectItem(id='ДИППК-п.р', abbreviations=[], name='Държавен изпит за придобиване на професионална квалификация - писмена работа по теория на професията + практика'),
        SubjectItem(id='ДИППК-тест', abbreviations=[], name='Държавен изпит за придобиване на професионална квалификация - писмен тест по теория на професията + практика'),
        SubjectItem(id='ДИППК-Д.Пр', abbreviations=[], name='Държавен изпит за придобиване на професионална квалификация - дипломен проект'),
        SubjectItem(id='ДИППК-пр', abbreviations=[], name='Държавен изпит за придобиване на професионална квалификация - практика '),
        SubjectItem(id='ИИ', abbreviations=[], name='Изобразително изкуство'),
        SubjectItem(id='ИНФ', abbreviations=[], name='Информатика'),
        *_lang_variations(SubjectItem(id='ИспЕ', abbreviations=['ИЕ', 'ИсЕ'], name='Испански език')),
        SubjectItem(id='ИСТ', abbreviations=['ИЦ'], name='История и цивилизация'),
        *_lang_variations(SubjectItem(id='ИтЕ', abbreviations=[], name='Италиански език')),
        SubjectItem(id='ИТ', abbreviations=[], name='Информационни технологии'),
        SubjectItem(id='МУЗ', abbreviations=[], name='Музика'),
        SubjectItem(id='МАТ', abbreviations=[], name='Математика'),
        *_lang_variations(SubjectItem(id='НЕ', abbreviations=[], name='Немски език')),
        *_lang_variations(SubjectItem(id='ПЕ', abbreviations=[], name='Португалски език')),
        SubjectItem(id='ПР', abbreviations=[], name='Предприемачество'),
        *_lang_variations(SubjectItem(id='РЕ', abbreviations=[], name='Руски език')),
        SubjectItem(id='ФА', abbreviations=[], name='Физика и астрономия'),
        SubjectItem(id='ФИЛ', abbreviations=[], name='Философия'),
        *_lang_variations(SubjectItem(id='ФрЕ', abbreviations=['ФЕ'], name='Френски език')),
        SubjectItem(id='ХООС', abbreviations=[], name='Химия и опазване на околната среда'),
        SubjectItem(id='ЧО', abbreviations=[], name='Човекът и обществото'),
        SubjectItem(id='ЧП', abbreviations=[], name='Човекът и природата'),
    ]

    db = get_db_engine()

    with Session(db) as session:
        for subject_item in default_subject_items:
            insert_or_update_subject(session, subject_item.id, subject_item.name, subject_item.abbreviations)

        session.commit()


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
