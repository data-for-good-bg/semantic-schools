from dataclasses import dataclass

# Constant used for working with bulgarian schools in foreign countries.
FOREIGN_COUNTRY = 'Чужбина'


@dataclass
class SubjectItem:
    """
    This class facilitates working with Subjects and the fact some of the
    have multiple abbreviations.
    The problem: For example Испански Език in different CSV files is found
    with ИЕ and ИспЕ. In the database we want to have just one subject abbreviation

    The `id` attribute is always an abbreviation of the subject, the `name` is
    the full name of the subject. The `abbreviations` is list of all other
    abbreviations known for the subject. This list could be empty.

    The `raw_strings()` method returns list of lowercased all possible
    abbreviations. This list is used to build a dictionary where the keys
    are abbreviations, the values are SubjectItem instances. Such dictionary
    is used in refine_csv for mapping the found subject abbreviation in certain
    CSV to the chosen one.

    In the database there is a table Subject which has the same columns - id,
    name and abbreviations. This table is used as source of information
    for SubjectItem instances.
    Check the function load_subject_abbr_map() below.

    The foreign languages subjects (English, Spanish, Russian, etc.) have
    variations with different levels - Б1, Б1.1 and Б2. They are treated as
    different subject items, so in the Subject table there are records for
    'АЕ', 'АЕ-Б1', 'АЕ-Б1.1', 'АЕ-Б2', and similar records for all other foreign
    languages.

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


def get_default_subjects() -> list[SubjectItem]:
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

    return default_subject_items