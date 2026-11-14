"""
Unit tests for csv_importer.refine_csv.extract_scores_dataframe.

The input data frames mimic the frames produced by load_json_to_dataframe:
column names contain '_' where the original JSON header had a newline
(e.g. 'Бр.\nМат(ООП)\nИ' becomes 'Бр._Мат(ООП)_И') and all values are strings.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from csv_importer.refine_csv import (
    expand_subject_column_in_score_dataframe,
    extract_scores_dataframe,
    load_json_to_dataframe,
)


def test_extract_scores_dataframe_happy_path() -> None:
    input_df = pl.DataFrame({
        'Област': ['София', 'Пловдив'],
        'Община': ['Столична', 'Пловдив'],
        'Училище': ['СМГ', 'ПГ'],
        'Код по НЕИСПУО': ['102004', '105201'],
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
        'Код по НЕИСПУО': ['102004'],
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
        'Код по НЕИСПУО': ['102004', '105201'],
        'Ср.усп._Мат(ООП)_И': ['4.42', '5.00'],
    })

    result = extract_scores_dataframe(input_df)

    assert set(result.columns) == {'school_admin_id', 'subject', 'score', 'people'}
    assert result['people'].to_list() == [0, 0]
    assert set(result['score']) == {'4.42', '5.00'}


def test_extract_scores_dataframe_missing_school_id_column_raises() -> None:
    input_df = pl.DataFrame({
        'Бр._Мат(ООП)_И': ['3'],
        'Ср.усп._Мат(ООП)_И': ['4.42'],
    })

    with pytest.raises(ValueError):
        extract_scores_dataframe(input_df)


# the school id column names supported by extract_scores_dataframe,
# add new supported names to this list
SCHOOL_ID_COLUMN_NAMES = ['Код по НЕИСПУО', 'Код по Админ']


@pytest.mark.parametrize('school_id_column', SCHOOL_ID_COLUMN_NAMES)
def test_extract_scores_dataframe_school_id_column(school_id_column: str) -> None:
    input_df = pl.DataFrame({
        'Област': ['София', 'Пловдив'],
        school_id_column: ['102004', '105201'],
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


def test_extract_scores_dataframe_from_json_file(tmp_path: Path) -> None:
    header = ['Област', 'Код по НЕИСПУО', 'Бр.\nМат(ООП)\nИ', 'Ср.усп.\nМат(ООП)\nИ']
    rows = [
        ['София', '102004', '3', '4.42'],
        ['Пловдив', '105201', '0', '0'],
    ]
    json_file = tmp_path / 'dzi-test.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump([header, *rows], f, ensure_ascii=False)

    raw_data = load_json_to_dataframe(str(json_file))
    assert raw_data.columns == ['Област', 'Код по НЕИСПУО', 'Бр._Мат(ООП)_И', 'Ср.усп._Мат(ООП)_И']

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
