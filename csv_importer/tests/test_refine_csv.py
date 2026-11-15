"""
Unit tests for csv_importer.refine_csv.

The input data frames for extract_scores_dataframe mimic the frames produced
by load_json_to_dataframe after column renaming: the school columns have
English names (school_admin_id, region, municipality, place, school) and
subject column names contain '_' where the original JSON header had a newline
(e.g. 'Бр.\\nМат(ООП)\\nИ' becomes 'Бр._Мат(ООП)_И'). All values are strings.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from csv_importer.refine_csv import (
    C_MUN,
    C_PLACE,
    C_REGION,
    C_SCHOOL_ID,
    C_SCHOOL_NAME,
    _beautify_place_column,
    _fill_empty_mun_and_place,
    _fill_school_id_special_cases,
    _refine_data,
    _unify_foreign_region,
    _rename_school_columns,
    expand_subject_column_in_score_dataframe,
    extract_scores_dataframe,
    load_json_to_dataframe,
)


# All five school-related columns that _rename_school_columns expects and
# renames, with sample values used across tests.
SCHOOL_COLUMNS_BG = ['Област', 'Община', 'Населено място', 'Училище']
SCHOOL_COLUMNS_EN = [C_REGION, C_MUN, C_PLACE, C_SCHOOL_NAME]


def _school_columns_row(region: str, mun: str, place: str, school: str) -> list[str]:
    return [region, mun, place, school]


# ---------------------------------------------------------------------------
# _rename_school_columns / _rename_columns
# ---------------------------------------------------------------------------

def test_rename_school_columns_renames_all_columns() -> None:
    input_df = pl.DataFrame({
        'Област': ['София'],
        'Община': ['Столична'],
        'Населено място': ['София'],
        'Училище': ['СМГ'],
        'Код по НЕИСПУО': ['102004'],
    })

    result = _rename_school_columns(input_df)

    assert set(result.columns) == {C_REGION, C_MUN, C_PLACE, C_SCHOOL_NAME, C_SCHOOL_ID}
    assert result.row(0, named=True) == {
        C_REGION: 'София',
        C_MUN: 'Столична',
        C_PLACE: 'София',
        C_SCHOOL_NAME: 'СМГ',
        C_SCHOOL_ID: '102004',
    }


# the school id column names supported by _rename_school_columns,
# add new supported names to this list
SCHOOL_ID_COLUMN_NAMES = ['Код по НЕИСПУО', 'Код по Админ']


@pytest.mark.parametrize('school_id_column', SCHOOL_ID_COLUMN_NAMES)
def test_rename_school_columns_school_id_column(school_id_column: str) -> None:
    input_df = pl.DataFrame({
        'Област': ['София'],
        'Община': ['Столична'],
        'Населено място': ['София'],
        'Училище': ['СМГ'],
        school_id_column: ['102004'],
    })

    result = _rename_school_columns(input_df)

    assert C_SCHOOL_ID in result.columns
    assert result.row(0, named=True)[C_SCHOOL_ID] == '102004'


def test_rename_school_columns_region_variant() -> None:
    input_df = pl.DataFrame({
        'Регион': ['София'],
        'Община': ['Столична'],
        'Населено място': ['София'],
        'Училище': ['СМГ'],
        'Код по НЕИСПУО': ['102004'],
    })

    result = _rename_school_columns(input_df)

    assert C_REGION in result.columns
    assert result.row(0, named=True)[C_REGION] == 'София'


def test_rename_school_columns_missing_expected_column_raises() -> None:
    # missing 'Училище' and school id column
    input_df = pl.DataFrame({
        'Област': ['София'],
        'Община': ['Столична'],
        'Населено място': ['София'],
    })

    with pytest.raises(RuntimeError, match='not found Bulgarian matchings'):
        _rename_school_columns(input_df)


def test_rename_columns_delegates_to_rename_school_columns() -> None:
    input_df = pl.DataFrame({
        'Област': ['София'],
        'Община': ['Столична'],
        'Населено място': ['София'],
        'Училище': ['СМГ'],
        'Код по НЕИСПУО': ['102004'],
        'Бр._БЕЛ(ООП)_З': ['5'],
    })

    result = _refine_data(input_df)

    assert C_REGION in result.columns
    assert C_MUN in result.columns
    assert C_PLACE in result.columns
    assert C_SCHOOL_NAME in result.columns
    assert C_SCHOOL_ID in result.columns
    # subject columns are passed through unchanged
    assert 'Бр._БЕЛ(ООП)_З' in result.columns


# ---------------------------------------------------------------------------
# _fill_empty_mun_and_place
# ---------------------------------------------------------------------------

def test_fill_empty_mun_and_place_fills_empty_strings_with_region() -> None:
    input_df = pl.DataFrame({
        C_REGION: ['София', 'Пловдив'],
        C_MUN: ['', 'Пловдив'],
        C_PLACE: ['', 'Пловдив'],
        C_SCHOOL_NAME: ['РУО София', 'ПГ'],
        C_SCHOOL_ID: ['0', '105201'],
    })

    result = _fill_empty_mun_and_place(input_df)

    assert result.row(0, named=True)[C_MUN] == 'София'
    assert result.row(0, named=True)[C_PLACE] == 'София'
    # non-empty values are kept unchanged
    assert result.row(1, named=True)[C_MUN] == 'Пловдив'
    assert result.row(1, named=True)[C_PLACE] == 'Пловдив'


def test_fill_empty_mun_and_place_fills_nulls_with_region() -> None:
    input_df = pl.DataFrame({
        C_REGION: ['София'],
        C_MUN: [None],
        C_PLACE: [None],
    })

    result = _fill_empty_mun_and_place(input_df)

    assert result.row(0, named=True)[C_MUN] == 'София'
    assert result.row(0, named=True)[C_PLACE] == 'София'


def test_refine_data_fills_empty_mun_and_place() -> None:
    input_df = pl.DataFrame({
        'Област': ['София'],
        'Община': [''],
        'Населено място': [''],
        'Училище': ['РУО София'],
        'Код по НЕИСПУО': ['0'],
    })

    result = _refine_data(input_df)

    assert result.row(0, named=True)[C_MUN] == 'София'
    assert result.row(0, named=True)[C_PLACE] == 'София'


# ---------------------------------------------------------------------------
# _fill_school_id_special_cases
# ---------------------------------------------------------------------------

def test_fill_school_id_special_cases_fills_ruo_ids() -> None:
    input_df = pl.DataFrame({
        C_REGION: ['Велико Търново', 'Пазарджик', 'София', 'София'],
        C_MUN: ['Велико Търново', 'Пазарджик', 'Столична', 'Столична'],
        C_PLACE: ['Велико Търново', 'Пазарджик', 'София', 'София'],
        C_SCHOOL_NAME: ['РУО Велико Търново', 'РУО Пазарджик', 'СМГ', 'РУО София'],
        C_SCHOOL_ID: ['', None, '102004', ''],
    })

    result = _fill_school_id_special_cases(input_df)

    assert result[C_SCHOOL_ID].to_list() == ['3400', '1300', '102004', '']


def test_refine_data_fills_school_id_special_cases() -> None:
    # mimics a dzi-2017 РУО row: no municipality, place and school id
    input_df = pl.DataFrame({
        'Област': ['Велико Търново'],
        'Община': [''],
        'Населено място': [''],
        'Училище': ['РУО Велико Търново'],
        'Код по НЕИСПУО': [''],
    })

    result = _refine_data(input_df)

    row = result.row(0, named=True)
    # the place is filled from the region and then beautified
    assert row[C_PLACE] == 'Велико Търново'
    assert row[C_SCHOOL_ID] == '3400'


# ---------------------------------------------------------------------------
# _unify_foreign_region
# ---------------------------------------------------------------------------

def test_unify_foreign_region_unifies_chuzhbina_variations() -> None:
    input_df = pl.DataFrame({
        C_REGION: ['ЧУЖБИНА', 'чужбина', 'софия', None],
        C_MUN: ['Чужбина - чужбина', 'СТОЛИЧНА', 'столична', 'Пловдив'],
        C_PLACE: ['Чужбина', 'София', 'София', 'Пловдив'],
    })

    result = _unify_foreign_region(input_df)

    assert result[C_REGION].to_list() == ['Чужбина', 'Чужбина', 'София', None]
    assert result[C_MUN].to_list() == ['Чужбина', 'Столична', 'Столична', 'Пловдив']
    # place column is not touched
    assert result[C_PLACE].to_list() == ['Чужбина', 'София', 'София', 'Пловдив']


def test_refine_data_unifies_foreign_region() -> None:
    input_df = pl.DataFrame({
        'Област': ['чужбина'],
        'Община': ['ЧУЖБИНА'],
        'Населено място': ['Чужбина'],
        'Училище': ['140. училище'],
        'Код по НЕИСПУО': ['1400001'],
    })

    result = _refine_data(input_df)

    row = result.row(0, named=True)
    assert row[C_REGION] == 'Чужбина'
    assert row[C_MUN] == 'Чужбина'


# ---------------------------------------------------------------------------
# _beutify_place_column
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    'place_value, expected',
    [
        ('ГР.СОФИЯ,КВ.ГОРНА БАНЯ', 'гр. София'),
        ('с.баня', 'с. Баня'),
        (' гр.софия ', 'гр. София'),
        ('София', 'София'),
        ('ВЕЛИКО ТЪРНОВО', 'Велико Търново'),
        ('Пловдив', 'Пловдив'),
        ('', ''),
        (None, None),
    ],
)
def test_beutify_place_column(place_value: Optional[str], expected: Optional[str]) -> None:
    input_df = pl.DataFrame({
        C_REGION: ['София'],
        C_PLACE: [place_value],
    })

    result = _beautify_place_column(input_df)

    assert result.row(0, named=True)[C_PLACE] == expected
    # other columns are not touched
    assert result.row(0, named=True)[C_REGION] == 'София'


# ---------------------------------------------------------------------------
# load_json_to_dataframe
# ---------------------------------------------------------------------------

def test_load_json_to_dataframe_renames_columns(tmp_path: Path) -> None:
    header = [
        'Област', 'Община', 'Населено място', 'Училище', 'Код по НЕИСПУО',
        'Бр.\nМат(ООП)\nИ', 'Ср.усп.\nМат(ООП)\nИ',
    ]
    rows = [
        ['София', 'Столична', 'София', 'СМГ', '102004', '3', '4.42'],
        ['Пловдив', 'Пловдив', 'Пловдив', 'ПГ', '105201', '0', '0'],
    ]
    json_file = tmp_path / 'dzi-test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([header, *rows], f, ensure_ascii=False)

    result = load_json_to_dataframe(str(json_file))

    assert result.columns == [
        C_REGION, C_MUN, C_PLACE, C_SCHOOL_NAME, C_SCHOOL_ID,
        'Бр._Мат(ООП)_И', 'Ср.усп._Мат(ООП)_И',
    ]


@pytest.mark.parametrize('school_id_column', SCHOOL_ID_COLUMN_NAMES)
def test_load_json_to_dataframe_school_id_column(tmp_path: Path, school_id_column: str) -> None:
    header = [
        'Област', 'Община', 'Населено място', 'Училище', school_id_column,
        'Бр.\nБЕЛ(ООП)\nЗ', 'Ср.усп.\nБЕЛ(ООП)\nЗ',
    ]
    rows = [
        ['София', 'Столична', 'София', 'СМГ', '102004', '5', '5.50'],
    ]
    json_file = tmp_path / 'dzi-test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([header, *rows], f, ensure_ascii=False)

    result = load_json_to_dataframe(str(json_file))

    assert C_SCHOOL_ID in result.columns
    assert result.row(0, named=True)[C_SCHOOL_ID] == '102004'


def test_load_json_to_dataframe_missing_school_columns_raises(tmp_path: Path) -> None:
    # missing Община, Населено място, Училище, and school id
    header = ['Област', 'Бр.\nБЕЛ(ООП)\nЗ']
    rows = [['София', '5']]
    json_file = tmp_path / 'dzi-test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([header, *rows], f, ensure_ascii=False)

    with pytest.raises(RuntimeError, match='not found Bulgarian matchings'):
        load_json_to_dataframe(str(json_file))


# ---------------------------------------------------------------------------
# extract_scores_dataframe
# ---------------------------------------------------------------------------

def test_extract_scores_dataframe_happy_path() -> None:
    input_df = pl.DataFrame({
        'school_admin_id': ['102004', '105201'],
        'Бр._Мат(ООП)_И': ['3', '0'],
        'Ср.усп._Мат(ООП)_И': ['4.42', '0'],
        'Бр._БЕЛ(ООП)_З': ['5', '7'],
        'Ср.усп._БЕЛ(ООП)_З': ['5.50', '6.00'],
    })

    result = extract_scores_dataframe(input_df)

    assert result.columns == ['school_admin_id', 'subject', 'people', 'score']
    expected = pl.DataFrame({
        'school_admin_id': ['102004', '102004', '105201', '105201'],
        'subject': ['БЕЛ(ООП)_З', 'Мат(ООП)_И', 'БЕЛ(ООП)_З', 'Мат(ООП)_И'],
        'people': ['5', '3', '7', '0'],
        'score': ['5.50', '4.42', '6.00', '0'],
    })
    assert_frame_equal(
        result.sort(['school_admin_id', 'subject']),
        expected.sort(['school_admin_id', 'subject']),
    )


def test_extract_scores_dataframe_parses_subject_names() -> None:
    input_df = pl.DataFrame({
        'school_admin_id': ['102004'],
        'Бр._Мат(ООП)_И': ['3'],
        'Ср.усп._Мат(ООП)_И': ['4.42'],
        'Бр._БЕЛ(ООП)_З': ['5'],
        'Ср.усп._БЕЛ(ООП)_З': ['5.50'],
        'Бр._АЕ(ООП)_B1-И': ['2'],
        'Ср.усп._АЕ(ООП)_B1-И': ['3.75'],
    })

    result = extract_scores_dataframe(input_df)

    assert set(result['subject']) == {'Мат(ООП)_И', 'БЕЛ(ООП)_З', 'АЕ(ООП)_B1-И'}
    assert result.height == 3


def test_extract_scores_dataframe_without_people_columns_adds_zero_people() -> None:
    input_df = pl.DataFrame({
        'school_admin_id': ['102004', '105201'],
        'Ср.усп._Мат(ООП)_И': ['4.42', '5.00'],
    })

    result = extract_scores_dataframe(input_df)

    assert set(result.columns) == {'school_admin_id', 'subject', 'score', 'people'}
    assert result['people'].to_list() == [0, 0]
    assert set(result['score']) == {'4.42', '5.00'}


def test_extract_scores_dataframe_from_json_file(tmp_path: Path) -> None:
    header = [
        'Област', 'Община', 'Населено място', 'Училище', 'Код по НЕИСПУО',
        'Бр.\nМат(ООП)\nИ', 'Ср.усп.\nМат(ООП)\nИ',
    ]
    rows = [
        ['София', 'Столична', 'София', 'СМГ', '102004', '3', '4.42'],
        ['Пловдив', 'Пловдив', 'Пловдив', 'ПГ', '105201', '0', '0'],
    ]
    json_file = tmp_path / 'dzi-test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([header, *rows], f, ensure_ascii=False)

    raw_data = load_json_to_dataframe(str(json_file))
    assert raw_data.columns == [
        C_REGION, C_MUN, C_PLACE, C_SCHOOL_NAME, C_SCHOOL_ID,
        'Бр._Мат(ООП)_И', 'Ср.усп._Мат(ООП)_И',
    ]

    result = extract_scores_dataframe(raw_data)

    expected = pl.DataFrame({
        'school_admin_id': ['102004', '105201'],
        'subject': ['Мат(ООП)_И', 'Мат(ООП)_И'],
        'people': ['3', '0'],
        'score': ['4.42', '0'],
    })
    assert_frame_equal(
        result.select('school_admin_id', 'subject', 'people', 'score').sort('school_admin_id'),
        expected.sort('school_admin_id'),
    )


# ---------------------------------------------------------------------------
# expand_subject_column_in_score_dataframe
# ---------------------------------------------------------------------------

@dataclass
class ExpectedSubjectParts:
    subject: Optional[str]
    preparation_type: str
    with_validation: bool
    level: str
    examination_type: Optional[str]


@pytest.mark.parametrize(
    'subject_value, expected',
    [
        ('БЕЛ(ООП)_З', ExpectedSubjectParts('БЕЛ', 'ООП', False, '', 'З')),
        ('Мат(ПП)_З', ExpectedSubjectParts('Мат', 'ПП', False, '', 'З')),
        ('ХООС(ПП)_З', ExpectedSubjectParts('ХООС', 'ПП', False, '', 'З')),
        ('АЕ(ООП)_B1-И', ExpectedSubjectParts('АЕ', 'ООП', False, 'Б1', 'И')),
        ('ФЕ(ПП)_B1.1-З', ExpectedSubjectParts('ФЕ', 'ПП', False, 'Б1.1', 'З')),
        ('НЕ(ООП)_B2-И', ExpectedSubjectParts('НЕ', 'ООП', False, 'Б2', 'И')),
        ('Пр(ПП)-В_И', ExpectedSubjectParts('Пр', 'ПП', True, '', 'И')),
        ('ДИППК-Д.Пр_З', ExpectedSubjectParts('ДИППК-Д.Пр', '-', False, '', 'З')),
    ],
)
def test_expand_subject_column_parses_subject_value(
    subject_value: str, expected: ExpectedSubjectParts
) -> None:
    input_df = pl.DataFrame({
        'school_admin_id': ['102004'],
        'subject': [subject_value],
        'people': ['5'],
        'score': ['5.50'],
    })

    result = expand_subject_column_in_score_dataframe(input_df)

    assert result.columns == [
        'school_admin_id', 'subject', 'people', 'score',
        'preparation_type', 'with_validation', 'level', 'examination_type',
    ]
    row = result.row(0, named=True)
    assert row['school_admin_id'] == '102004'
    assert row['people'] == '5'
    assert row['score'] == '5.50'
    assert row['subject'] == expected.subject
    assert row['preparation_type'] == expected.preparation_type
    assert row['with_validation'] == expected.with_validation
    assert row['level'] == expected.level
    assert row['examination_type'] == expected.examination_type


def test_expand_subject_column_multiple_rows() -> None:
    input_df = pl.DataFrame({
        'school_admin_id': ['102004', '105201', '100190'],
        'subject': ['БЕЛ(ООП)_З', 'АЕ(ООП)_B1-И', 'Пр(ПП)-В_И'],
        'people': ['5', '2', '7'],
        'score': ['5.50', '3.75', '6.00'],
    })

    result = expand_subject_column_in_score_dataframe(input_df)

    expected = pl.DataFrame({
        'school_admin_id': ['102004', '105201', '100190'],
        'subject': ['БЕЛ', 'АЕ', 'Пр'],
        'people': ['5', '2', '7'],
        'score': ['5.50', '3.75', '6.00'],
        'preparation_type': ['ООП', 'ООП', 'ПП'],
        'with_validation': [False, False, True],
        'level': ['', 'Б1', ''],
        'examination_type': ['З', 'И', 'И'],
    })
    assert_frame_equal(result, expected)


def test_expand_subject_column_unmatched_subject_value_yields_nulls() -> None:
    # the subject regex only matches levels B1, B1.1 and B2, so a value like
    # 'АЕ(ООП)_B2.1-И' does not match at all and the extracted columns become null
    input_df = pl.DataFrame({
        'school_admin_id': ['102004'],
        'subject': ['АЕ(ООП)_B2.1-И'],
        'people': ['2'],
        'score': ['3.75'],
    })

    result = expand_subject_column_in_score_dataframe(input_df)

    row = result.row(0, named=True)
    assert row['subject'] is None
    assert row['preparation_type'] == '-'
    assert row['with_validation'] is False
    assert row['level'] == ''
    assert row['examination_type'] is None
