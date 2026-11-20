#!/usr/bin/env python3

"""
This script contains functions for working with NVO and DZI CSV files provided
by data.egov.bg.

It is supposed that these functions will be used by another script which
will convert/import the data into postgres, GraphDB, etc.

It can be used as a standalone app by passing one CSV file to it. This is
dev use case - it calls all main functions on the provided CSV file.
"""

import pandas as pd
import polars as pl
import sys
import logging
import os
import re
import json

from io import StringIO
from typing import Optional


from .runtime import getLogger
from .db_manage import load_subject_abbr_map
from .models import SubjectItem, FOREIGN_COUNTRY, get_default_subjects


logger = getLogger(__name__)


# List of regular expressions which will be translated no matter where
# in the column name are found. The order is important.
COL_RE_TRANSLATION = [
    ('област', 'region'),
    ('регион', 'region'),
    ('община', 'municipality'),
    ('населено място', 'place'),
    ('населено  място', 'place'),
    ('училище', 'school'),
    ('код по админ', 'school_admin_id'),
    ('код по неиспуо', 'school_admin_id'),
    ('код', 'school_admin_id'),
    ('mat', 'мат'),
    ('\)з', ')'), # there's one special case in dzi-2022
    (' \(мах 100 т\)', ''), #nov-4-2018
    ('\(пп\)', ''), # dzi-2022
    ('\(ооп\)', ''), # dzi-2022
    (' з', ''),
    (' b(1|1.1|2)-з', r'-б\1'),
    ('диппк-пр\.', 'диппк-пр'),
]

# List of regular expressions which will be translated only if they
# are found at the beginning or at the end of the column name.
# The order is important.
COL_RE_TRANSLATION_SPECIAL_POSITIONS = [
    ('явили се', 'people'),
    ('ср\. успех в точки', 'score'),
    ('ср\.успех', 'score'),
    ('ср\.усп\.', 'score'),
    ('ср\.усп', 'score'),

    ('бр\.', 'people'),
    ('брой', 'people'),
]

# Some of the DZI CSV files contain columns titled '2дзи' with aggregated
# information about 2nd DZI (i.e. non BEL DZI),
# Some of the DZI CSV files contain columns titled 'общо' with aggregated
# information for all DZI.
# If not removed these columns are treated as another subject, so we
# delete them.
SUBJECTS_TO_REMOVE = ['2дзи', 'общо']

# Subject columns in the data frames are structured like this
# 'БЕЛ people' and 'БЕЛ score'. The two constants are the indexes of
# subject name component and attribute name component in such column names.
SBJ_IDX = 0
ATTR_IDX = 1

C_SCHOOL_ID = 'school_admin_id'
C_SCHOOL_NAME = 'school'
C_REGION = 'region'
C_MUN = 'municipality'
C_PLACE = 'place'
C_PEOPLE = 'people'
C_SCORE = 'score'


def refine_original_col_name(value: str) -> str:
    """
    This function changes original column names.
    * translates known texts from Bulgarian to English
    * lowers all letters
    * removes redundant information or characters
    """

    logger.verbose_info('value %s', value)

    value = value.replace('"', '')
    value = value.lower()
    logger.verbose_info('value %s', value)

    while '  ' in value:
        value = value.replace('  ', ' ')
    logger.verbose_info('value %s', value)


    for regex, repl in COL_RE_TRANSLATION:
        value = re.sub(regex, repl, value)
        value = value.strip()
    logger.verbose_info('value %s', value)

    for base_regex, repl in COL_RE_TRANSLATION_SPECIAL_POSITIONS:
        value = re.sub(f'^{base_regex}', repl, value)
        value = re.sub(f'{base_regex}$', repl, value)
        value = value.strip()
    logger.verbose_info('value %s', value)

    # sometimes there's missing space between the subject name and
    # the score
    if 'score' in value and not value.startswith('score') and ' score' not in value:
        value = value.replace('score', ' score')
    logger.verbose_info('value %s', value)

    return value


def order_attr_in_subject_column_names(col_names):
    """
    This function re-orders the words in column names like
    'people БЕЛ' and 'score БЕЛ' into 'БЕЛ people' 'БЕЛ score'.
    Such naming would allow us to order the columns in groups by subject.
    This is needed, because in th NVO 4 files the columns are not paired by
    subject (as they are in NVO 7 files).
    """
    result = []

    for col_name in col_names:
        if col_name.startswith('score ') or col_name.startswith('people '):
            try:
                f, s = col_name.split(' ')
                result.append(f'{s} {f}')
            except ValueError:
                logger.exception('Failed to handle column: %s', col_name)
                raise

        else:
            result.append(col_name)

    return result


def is_people_column(col_name: str) -> bool:
    return col_name.endswith(' people')


def is_score_column(col_name: str) -> bool:
    return col_name.endswith(' score')


def is_subject_column(col_name: str) -> bool:
    """
    Return True if the column is a subject column, otherwise False.
    A subject column is column which carries information for the number of
    people attended to examination of given subject ('<subj> people')
    and the score for certain subject ('<subj> score').
    """
    return is_people_column(col_name) or is_score_column(col_name)


def is_particular_subject_column(col_name: str, subject: str) -> bool:
    """
    Checks if the col_name is particular subject.
    """
    return is_subject_column(col_name) and col_name.startswith(f'{subject} ')


def infer_max_possible_nvo_score(data: pd.DataFrame) -> float:
    """
    Infers the max possible score based on the data found in the data frame.

    For NVO the maximum possible score:
    * was 65 points for several years
    * after that the max possible score is 100 points
    """

    assert 'score' in data.columns, \
        'The data frame should contain score column in order to infer the max possible score.'
    max_score = data['score'].max()
    logger.verbose_info('max score value calculated is: %s', max_score)

    if max_score <= 6.00:
        return 6.00

    if max_score <= 65.00:
        return 65.00

    return 100.00


def load_json_to_dataframe(input_file: str) -> pl.DataFrame:
    """
    Loads an input file as json into a polars dataframe.
    The first line is treated as column names.
    """
    with open(input_file, 'rt') as f:
        raw_data = json.load(f)

    header, *rows = raw_data
    header = [
        # the column names in the json file contain newline character, replace it
        h.replace('\n', ' ')
        for h in header
    ]

    raw_data = pl.DataFrame(rows, schema=header, orient="row")

    return _refine_data(raw_data)


def _rename_school_columns(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    Renames the columns for region, municipality, place (city/village),
    and school name and school id from Bulgarian to English.
    """

    mapping = {
        'Област': C_REGION,
        'Регион': C_REGION,

        'Община': C_MUN,

        'Населено място': C_PLACE,
        'Населено  място': C_PLACE,

        'Училище': C_SCHOOL_NAME,

        'Код по НЕИСПУО': C_SCHOOL_ID,
        'Код по Админ': C_SCHOOL_ID
    }

    # only rename columns that actually exist (polars rename requires all
    # mapping keys to be present)
    existing_mapping = {
        k: v for k, v in mapping.items() if k in input_df.columns
    }
    result = input_df.rename(existing_mapping)

    expected_columns = set([C_REGION, C_MUN, C_PLACE, C_SCHOOL_NAME, C_SCHOOL_ID])

    not_found_columns = expected_columns - set(result.columns)
    if not_found_columns:
        raise RuntimeError((
            'The input dataframe is expected to contain columns in Bulgarian'
            ' which will be translated to English. For the following '
            f' columns were not found Bulgarian matchings: {not_found_columns}'
        ))

    return result


def _fill_empty_mun_and_place(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    Some of the input files contain results not for a school, but for РУО -
    Регионално управление на образованието.
    These lines could have empty municipality and place columns.
    This function fills them with the value of the region or municipality.
    """

    # fill empty municipality from region
    mun_filled = input_df.with_columns(
        pl.when(pl.col(C_MUN).is_null() | (pl.col(C_MUN).cast(pl.String).str.strip_chars() == ''))
        .then(pl.col(C_REGION))
        .otherwise(pl.col(C_MUN))
        .alias(C_MUN)
    )

    # fill empty place from municipality
    place_filled = mun_filled.with_columns(
        pl.when(pl.col(C_PLACE).is_null() | (pl.col(C_PLACE).cast(pl.String).str.strip_chars() == ''))
        .then(pl.col(C_MUN))
        .otherwise(pl.col(C_PLACE))
        .alias(C_PLACE)
    )

    return place_filled


def _validate_non_empty_columns(input_df: pl.DataFrame) -> None:
    """
    Validates that certain columns are non-empty.
    Raises RuntimeError listing the offending columns otherwise.
    """
    samples: list[str] = []
    for col in (C_REGION, C_MUN, C_PLACE, C_SCHOOL_ID, C_SCHOOL_NAME):
        is_empty = (
            pl.col(col).is_null()
            | (pl.col(col).cast(pl.String).str.strip_chars() == '')
        )
        filtered_df = input_df.filter(is_empty)
        if filtered_df.height > 0:
            samples.append(f'Column {col} is empty in some rows, samples are: {filtered_df.head()}')

    if samples:
        samples_str = '\n'.join(samples)
        raise RuntimeError(
            'The input dataframe is expected to contain non-empty values in '
            'the region, municipality and place columns, but empty values '
            f'were found in, check this: \n {samples_str}'
        )


def _fill_school_id_special_cases(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    In the DZI CSV for 2017 there are results for two РУО without school_admin_id
    This function fills the school_admin_id, because we know it from other years.

    РУО Велико Търново id is 3400
    РУО Пазарджик id is 1300
    """
    school_id_missing = (
        pl.col(C_SCHOOL_ID).is_null()
        | (pl.col(C_SCHOOL_ID).cast(pl.String).str.strip_chars() == '')
    )

    return input_df.with_columns(
        pl.when(school_id_missing & (pl.col(C_PLACE) == 'Велико Търново'))
        .then(pl.lit('3400'))
        .when(school_id_missing & (pl.col(C_PLACE) == 'Пазарджик'))
        .then(pl.lit('1300'))
        .otherwise(pl.col(C_SCHOOL_ID))
        .alias(C_SCHOOL_ID)
    )


def _unify_foreign_region(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    There are rows which are for region Чужбина, which in different files
    is written in different way.
    This function unifies all its possible values in the columns region and
    municipality.
    """
    return input_df.with_columns([
        pl.when(pl.col(col).cast(pl.String).str.to_lowercase().str.contains('чужбина'))
        .then(pl.lit(FOREIGN_COUNTRY))
        .otherwise(pl.col(col))
        .str.to_titlecase()
        .alias(col)
        for col in (C_REGION, C_MUN)
    ])


def _beautify_place_column(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    Formats the place column in a standard way:
    * values like ГР.СОФИЯ,КВ.ГОРНА БАНЯ are reduced to the city part
    * values with a prefix like 'гр.'/'с.' are formatted as 'гр. София'
    * all other values get only their first letter upper-cased
    """
    # values like ГР.СОФИЯ,КВ.ГОРНА БАНЯ -> keep only the city part
    place = pl.col(C_PLACE).cast(pl.String).str.split(',').list.first()

    # split `гр.София` or `с.Баня` into `гр`, `София` or `с`, `Баня`
    parts = place.str.split('.')

    # ensure prefix is always lowercased
    prefix_part = parts.list.first().str.strip_chars().str.to_lowercase()

    # make the name part title-case (TITLE CASE -> "Title Case")
    name_part = parts.list.get(1).str.strip_chars().str.to_titlecase()

    # make the name-only case also title-case
    name_only = place.str.strip_chars().str.to_titlecase()

    return input_df.with_columns(
        pl.when(place.str.contains('.', literal=True))
        .then(prefix_part + pl.lit('. ') + name_part)
        .otherwise(name_only)
        .alias(C_PLACE)
    )


def _refine_data(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    The input_df is assumed to be the raw dataframe after the raw json was
    loaded.
    The function take cares to do different column renamings, data formatting
    which make later data processing easier.
    """

    input_df = _rename_school_columns(input_df)
    input_df = _fill_empty_mun_and_place(input_df)
    input_df = _fill_school_id_special_cases(input_df)
    input_df = _unify_foreign_region(input_df)
    input_df = _beautify_place_column(input_df)

    _validate_non_empty_columns(input_df)

    return input_df


def _extract_long_scores_dataframe(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    The input dataframe is assumed to be the one after refining the raw data
    loaded from json/csv.
    It should be with C_SCHOOL_ID column and to be in
    the "wide" form, where there's a pair of columns for each subject - one
    for the number of attended students and one for the average score.

    There's an exception: the August-September DZI session does not contain
    column for the number of students.

    The result dataframe structure will be in the following "long" form:
    * column `subject` containing the subject with all possible attributes,
      examples are БЕЛ(ООП)-З, АЕ-(ПП)-B1-З, ..
    * column `people` representing the number of students; it will be always
      zero for the August-September DZI sessions
    * column `score` representing the average score
    """

    columns = [
        c
        for c in input_df.columns
        if c == C_SCHOOL_ID or c.startswith('Бр.') or c.startswith('Ср.усп.')
    ]

    scores_data_wide = (
        input_df
        .select(columns)
    )

    result = (
        # unpivot the data to structure where there's row (`school_admin_id`, `col`, `value`)
        # for each `Бр....` or `Ср.Усп...` column
        scores_data_wide.unpivot(
            index=C_SCHOOL_ID,
            on=[c for c in scores_data_wide.columns if c != C_SCHOOL_ID],
            variable_name='col',
            value_name='value',
        )
        # add columns `metric` and `subject` to each row, extract their from
        # the value of column `col` with regex
        # `Бр._БЕЛ(ООП)_З` will become (metric=`Бр.`, subject=`БЕЛ(ООП)_З`)
        # `Ср.усп._ГИ(ПП)_З` will become (metric=`Ср.усп.`, subject=`ГИ(ПП)_З`)
        .with_columns(
            pl.col('col').str.extract(r'^(Бр.|Ср.усп.)[ ]*(.*)$', 1).alias('metric'),
            pl.col('col').str.extract(r'^(Бр.|Ср.усп.)[ ]*(.*)$', 2).alias('subject'),
        )
        # pivot the data to dataframe with rows (`school_admin_id`, `subject`, `Бр.`, `Ср.Усп.`)
        .pivot(values='value', index=[C_SCHOOL_ID, 'subject'], on="metric")
    )

    # when the input data contains no columns starting with `Бр.` the pivot
    # above does not produce a `Бр.` column - in that case no people attended
    # the examinations, so the result gets a `people` column with value 0
    rename_map = {
        'Бр.': C_PEOPLE,
        'Ср.усп.': C_SCORE,
    }
    result = result.rename({
        metric: name for metric, name in rename_map.items() if metric in result.columns
    })

    # fill in C_PEOPLE column for the August-September DZI sessions when
    # there's no information for the number of students
    if C_PEOPLE not in result.columns:
        result = result.with_columns(pl.lit('').alias(C_PEOPLE))

    result = result.with_columns(
        pl.when(pl.col(C_PEOPLE).str.strip_chars().is_in(['', '-']))
        .then(pl.lit(0))
        .otherwise(pl.col(C_PEOPLE))
        .cast(pl.Int64, strict=True)
        .alias(C_PEOPLE)
    )

    return result


def _expand_subject_column_in_score_dataframe(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    The input dataframe structure should be:
    * column `school_admin_id`
    * column `subject` containing the subject with all possible options
    * column `people` representing the number of students
    * column `score` representing the average score

    The function takes the `subject` column and expands it in the following
    columns:
    * `subject` - the abbreviation of the subject - МАТ, БЕЛ, АЕ, ФА, ....
    * `preparation_type` - `ООП` or `ПП` (`Общообразователна подготовка` или `Профилирана подготовка`)
    * `with_validation` - boolean (when В /Cyrillic/ for "Валидация" is matched)
    * `level` - currently used only for foreign language subjects,
                possible values (cyrillic chars) `Б1`, `Б1.1`, `Б2`
    * `examination_type` - `З` or `И` - (`Задължителен` или `Избираем`)

    These columns are extracted from the value of the `subject` column which
    carries the additional classification values.
    """
    rows_with_empty_subject = input_df.filter(
        pl.col('subject').is_null() | (pl.col('subject').cast(pl.String).str.strip_chars() == '')
    )
    if rows_with_empty_subject.height > 0:
        raise ValueError(
            'The subject column contains null or empty values. '
            f'Sample rows: {rows_with_empty_subject.head(5)}'
        )


    # This regex matches the following values:
    # * БЕЛ(ООП)_З -> (БЕЛ, ООП, false, none, З)
    # * ФЕ(ПП)_B1-З -> (ФЕ, ПП, false, Б1, З)
    # * ХООС(ПП)_З -> (ХООС, ПП, false, none, З)
    # * ДИППК-Д.Пр_З -> (ДИППК-Д.Пр, none, false, none, З)
    # * Пр(ПП)-В_И -> (Пр, ПП, true, none, И)
    # Using non-capturing groups where if don't need it in the result groups,
    # this way the groups of interest are with sequential indexes.
    subject_re = r'^([А-Яа-я-\.]+)[ ]*(?:\((ПП|ООП)\))?(?:-(В))? (?:([ABC][12](?:\.[12])?)-)?(З|И)$'

    subject_match = pl.col('subject').str.extract(subject_re, 1)
    subject_expr = (
        pl.when(subject_match.is_null())
        .then(pl.lit('ERR ') + pl.col('subject'))
        .otherwise(subject_match)
    )

    result = (
        input_df.with_columns(
            subject_expr.alias('subject'),
            pl.col('subject').str.extract(subject_re, 2).fill_null('-').alias('preparation_type'),
            pl.col('subject').str.extract(subject_re, 3).is_not_null().alias('with_validation'),
            pl.col('subject').str.extract(subject_re, 4).fill_null('').str.replace_many({'A': 'А', 'B': 'Б', 'C': 'С'}).alias('level'),
            pl.col('subject').str.extract(subject_re, 5).alias('examination_type'),
        )
    )

    rows_with_err = result.filter(pl.col('subject').str.starts_with('ERR '))
    if rows_with_err.height > 0:
        raise ValueError(
            'Cannot parse subject for the following rows. '
            f'Sample rows: {rows_with_err.head(5)}'
        )

    return result


def _map_subjects(input_df: pl.DataFrame, subject_mapping: dict[str, SubjectItem]) -> pl.DataFrame:
    """
    The input dataframe should have a `subject` column which contains only subject
    abbreviation (no other subject attributes).
    The subject_mapping represents mapping between all known subject abbreviations
    and the corresponding subject (SubjectItem object).

    The function will first check if the input dataframe contains a subject
    abbreviation which is not found in the subject_mapping and will raise
    a ValueError in this case. It will also raise a ValueError if the
    `subject` column contains null or empty values.

    After that the function will map the subject abbreviation to the corresponding
    SubjectItem.id.
    """
    # the keys of subject_mapping are lowercased abbreviations, while the
    # values in the `subject` column keep their original case
    unique_subjects = input_df.get_column('subject').unique().to_list()

    unknown_subjects = sorted(s for s in unique_subjects if s.lower() not in subject_mapping)
    if unknown_subjects:
        raise ValueError(f'Cannot find subjects for abbreviations {unknown_subjects}.')

    abbr_to_id = {abbr: item.id for abbr, item in subject_mapping.items()}
    return input_df.with_columns(
        pl.col('subject')
        .str.to_lowercase()
        .replace_strict(abbr_to_id, return_dtype=pl.String)
        .alias('subject')
    )


def extract_scores_dataframe(input_df: pl.DataFrame, subject_mapping: Optional[dict[str, SubjectItem]] = None) -> pl.DataFrame:
    """
    The input dataframe is assumed to be the one after refining the raw data
    loaded from json/csv.

    The output dataframe will be in the long form with the following columns:

    * `school_admin_id`
    * `subject` name of the subject
    * `preparation_type` - `ООП` or `ПП` (`Общообразователна подготовка` или `Профилирана подготовка`)
    * `with_validation` - boolean (when В /Cyrillic/ for "Валидация" is matched)
    * `level` - currently used only for foreign language subjects,
                possible values (cyrillic chars) `Б1`, `Б1.1`, `Б2`
    * `examination_type` - `З` or `И` - (`Задължителен` или `Избираем`)
    * `people` representing the number of students
    * `score` representing the average score

    From the result dataframe will be removed all rows where score and people
    columns are NaN or zero.

    The function will raise a ValueError exception in case there's subject
    which cannot be recognized or in case the `subject` column contains
    null or empty values.

    """
    if subject_mapping is None:
        subject_mapping = {}
        for item in get_default_subjects():
            for raw_str in item.raw_strings():
                subject_mapping[raw_str] = item

    scores_data = _extract_long_scores_dataframe(input_df)
    scores_data = _expand_subject_column_in_score_dataframe(scores_data)
    scores_data = _map_subjects(scores_data, subject_mapping)

    # remove the rows where both `score` is NaN or zero -
    # such rows carry no examination information; the cast to float makes
    # the check work for string values ('0', '4.42') as well
    score = pl.col(C_SCORE).cast(pl.Float64, strict=False)
    scores_data = scores_data.filter(
        ~(
            (score.is_null() | score.is_nan() | (score == 0))
        )
    )

    return scores_data


def extract_schools_dataframe(input_df: pl.DataFrame) -> pl.DataFrame:
    """
    The input dataframe is assumed to be the one after refining the raw data
    loaded from json/csv.
    """

    return input_df.select(
        C_SCHOOL_ID,
        C_SCHOOL_NAME,
        C_REGION,
        C_MUN,
        C_PLACE
    )



def get_unique_subjects(input_df: pl.DataFrame) -> list[str]:
    return (
        input_df.select(
            pl.col('subject').unique()
        )
        .to_series()
        .sort()
        .to_list()
    )


def load_csv(file: str) -> StringIO:
    '''
    This function pre-loads the specified file into StringIO and performs
    some really basic mechanical changes on the contents.

    1. Using 'utf-8-sig' encoding to handle the BOM csv files provided
        by data.egov.bg
        Some of the CSV files contain the BOM mark not only at the beginning
        of the file, but also inside the first value on the first line.
        That's why below we replace the sequence '\ufeff' everywhere.
        https://en.wikipedia.org/wiki/Byte_order_mark
        https://docs.python.org/3/howto/unicode.html
        https://stackoverflow.com/questions/13590749/reading-unicode-file-data-with-bom-chars-in-python

    2. It also replaces unusual characters which are found in some of the CSV files

    3. Recent CSV files for DZI data contain new-line character in the CSV column names
       As result the header line of the CSV file is not a single line,
       it is spread at multiple lines, it looks like this:
       ```
        "Област","Община","Населено място","Училище","Код по НЕИСПУО","Бр.
        БЕЛ(ООП)
        З","Ср.усп.
        БЕЛ(ООП)
        З","Бр.
        Мат(ПП)
        З","Ср.усп.
        Мат(ПП)
        З",
       ```
       This function converts these many lines into a single line.
    '''

    # The first unicode sequence is the BOM mark,
    # The second one is another weird unicode sequence found in a column name.
    # The third item is because one of the files contains: "<BOM>""Област"""
    #   So the <BOM> will be replaced, then we handle the tripled quotes
    #   It is handled by this special way, because it is not good idea to handle
    #   tripled quotes in the whole file.
    to_replace = {
        '\ufeff': '',
        '\u00a0': '',
        '"""Област"""': '"Област"'
    }

    result = StringIO()

    with open(file, 'rb') as f:
        # First loop: find and fix only the header line
        header_buffer = ''
        header_written = False

        for line in f:
            # Decode and strip line endings
            line_str = line.decode('utf-8-sig').rstrip('\n\r')

            # Apply character replacements
            for old_v, new_v in to_replace.items():
                line_str = line_str.replace(old_v, new_v)

            if header_buffer:
                header_buffer += ' ' + line_str
            else:
                header_buffer = line_str

            # Check if header is complete (even number of quotes)
            if header_buffer.count('"') % 2 == 0:
                # Then write the header
                result.write(header_buffer + '\n')
                header_buffer = ''
                header_written = True

                # The current line has already been consumed into header_buffer
                # We need to add the next lines to remaining_lines
                break

        # If we exited the loop without finding a complete header
        if not header_written:
            raise RuntimeError('Failed to parse CSV header line.')

        # Second loop: write all remaining lines with character replacements only
        for line in f:
            line_str = line.decode('utf-8-sig')
            for old_v, new_v in to_replace.items():
                line_str = line_str.replace(old_v, new_v)
            result.write(line_str)

    result.seek(0)
    return result


def fill_empty_cells_from_previous(input: list[str]) -> list[str]:
    """
    Takes a list of strings as input and returns another  assert subject_cols_count > 0list in which the
    where empty elements will be filled with the value from the preceding
    element.

    Example:

    ['','','a','','b',''] -> ['', '', 'a', 'a', 'b','b']

    This is used to fill column names in the cases where the pair of columns
    describe the same subject, but only one of them is filled.

    """
    if not input:
        return input

    result = input.copy()
    for i in range(1, len(result)):
        if result[i] == '':
            result[i] = result[i-1]

    return result


def refine_csv_column_names(input: StringIO) -> StringIO:
    """
    The function gets the raw CSV input removes all non-CSV lines and
    more importantly - re-organizes the CSV column names in a way which
    is easier for automatic processing.

    There CSV files for NVO and DZI come in several formats.

    Currently this function supports several variations and does not
    support these files:
    * dzi-2016 -> contains three columns "Училище" and does not contain "Код по Админ"
    * nvo-4-2015 -> does not contain "Код по Админ".
    * nvo-7-2016 -> does not contain "Код по Админ"

    Rest of the CSV files are in a form which this function supports.

    Here are more details about the supported formats and their variations:

    1. All supported formats contain a line with column names which starts with
    column Област or in one case Регион.

    Examples:
    * nvo-4-2019
        "Област","Община","Населено място","Код","Училище","Явили се МАТ","Явили се БЕЛ","Явили се ЧО","Явили се ЧП","Ср. успех в точки МАТ","Ср. успех в точки БЕЛ","Ср. успех в точки ЧО","Ср. успех в точки ЧП"
    * nvo-4-2022
        "Област","Община","Населено място","Училище","Код по АДМИН","БЕЛ Явили се","БЕЛ Ср. успех в точки","МАТ Явили се","МАТ  Ср. успех в точки"

    2. In some cases this line is preceded by several additional lines
    which describe what the file is about. These lines are not well structured
    and this function ignores them.
    There's loop below which skips all lines before the line starting with
    'Област'.

    Examples: nvo-7-2018

    3. In some case the line with column names is followed by one or two
    lines which contain additional descriptors (or options) for the columns.

    Several examples:
    * nvo-4-2023
        "Област","Община","Населено място","Училище","Код по Админ","БЕЛ","","МАТ",""
        "","","","","","Явили се","Ср. успех в точки","Явили се","Ср. успех в точки"

    * nvo-7-2021
        "Област","Община","Населено място","Училище","Код по Админ","Явили се","Ср. успех в точки","Явили се","Ср. успех в точки"
        "","","","","","БЕЛ","БЕЛ","МАТ","МАТ"

    * dzi-2023
            "Област","Община","Населено място","Училище","Код по Админ","БЕЛ(ООП)","","Мат(ПП)","","Ист(ПП)","".....
            "","","","","","З","","З","","З","".......
            "","","","","","Бр.","Ср.усп.","Бр.","Ср.усп.","Бр.","Ср.усп."......

    These two or three lines are merged by concatenating the values with
    space as separator (only where options are non-empty).

    For nvo-4-2023 we'll have columns like:
    "БЕЛ Явили се", "БЕЛ Ср. успех в точки"

    For nvo-7-2021 wе'll have columns like:
    "Явили се БЕЛ" "Ср. успех в точки БЕЛ"

    For dzi-2023 we'll have columns like:
    "БЕЛ(ООП) З Бр.", "БЕЛ(ООП) З Ср.усп."

    NB: In dzi-2023 example there is column "БЕЛ(ПП)" followed by empty column,
    then "Мат(ПП)" and again empty column. The empty columns are filled
    from their preceding column.

    ---

    In all three variations the function constructs a single line
    with column names.
    After that this line is partially translated to english. All variations
    of 'Явили се' are translated to the term 'people', all variations of
    'Среден успех' are translated to 'score'.
    The function does also some other replacements in order to remove
    insignificant data.

    As it is shown in the examples above there are files where 'Явили се' and
    'Среден успех' are at the beginning of the column name, in other files
    it is at the end of the column name.

    After the translation we have 'people' and 'score' either at the beginning
    or at the end of the column names.

    The function re-organizes this by putting the subject name at the beginning
    in all subject columns, all of them become:
    'БЕЛ score', 'БЕЛ people', 'MAT score', 'MAT people', ....

    This way we can sort the columns by subject name. This is important
    because in some files the subject columns are paired, but in some files
    we have 'Явили се' columns for all subjects, then 'Среден успех' columns
    for all subjects.

    At the end this function returns the input StringIO changed to contain
    only one line with column names. This way it is ready to be imported
    by Pandas.
    """

    input.seek(0)

    # This loop finds the line with the original column names and
    # also the lines which contain additional column options
    column_names_line = None
    column_option_lines = []
    buffered_line = None
    for line in input:
        if column_names_line is None:
            if line.startswith('"Област') or line.startswith('"Регион'):
                column_names_line = line.strip()
        else:
            if line.startswith('""'):
                column_option_lines.append(line.strip())
            else:
                # buffer this line, we need to added it to the output
                buffered_line = line
                break

    if not column_names_line:
        raise RuntimeError('Cannot find line with column names.')
    logger.verbose_info('column_names_line: %s', column_names_line)

    output = StringIO()

    # get the original column lines, remove the double quotes
    new_col_names = [
        c.replace('"', '')
        for c in column_names_line.split(',')
    ]
    logger.verbose_info('new_col_names: %s', new_col_names)

    # In some files there are columns without name. These columns take
    # the name of the previous column.
    new_col_names = fill_empty_cells_from_previous(new_col_names)
    logger.verbose_info('new_col_names: %s', new_col_names)

    # Merge the new column names with the values of the lines with column
    # options
    for option_line in column_option_lines:
        options = [
            c.replace('"', '')
            for c in option_line.split(',')
        ]
        logger.verbose_info('options: %s', options)
        options = fill_empty_cells_from_previous(options)
        logger.verbose_info('options: %s', options)

        # merge new_col_names with the current options and produce
        # list with the merged values
        ex_col_names = []
        for col_name, option in zip(new_col_names, options):
            # strip is important for the empty options
            new_col_name = f'{col_name} {option}'.strip()
            ex_col_names.append(new_col_name)
        new_col_names = ex_col_names

        logger.verbose_info('options: %s', options)
        logger.verbose_info('new_col_names: %s', new_col_names)

    # translate  columns
    for i in range(len(new_col_names)):
        new_col_names[i] = refine_original_col_name(new_col_names[i])
    logger.verbose_info('new_col_names: %s', new_col_names)

    # organize all subject column names to contain subject at the beginning
    new_col_names = order_attr_in_subject_column_names(new_col_names)
    logger.verbose_info('new_col_names: %s', new_col_names)

    # construct the new column names line
    new_column_names_lines = ','.join(new_col_names) + os.linesep
    logger.verbose_info('new_column_names_lines: %s', new_column_names_lines)

    output.write(new_column_names_lines)

    if buffered_line:
        logger.verbose_info('buffered_line: %s', buffered_line)
        output.write(buffered_line)

    # copy add all other lines into the result
    for line in input:
        output.write(line)

    return output


def refine_data(csv_data: StringIO, subject_mapping: dict[str, SubjectItem]) -> pd.DataFrame:
    """
    This function loads a CSV file into pandas DataFrame and
    refines the data.
    """

    csv_data.seek(0)
    data = pd.read_csv(csv_data)

    # convert school id column to str
    data['school_admin_id'] = data['school_admin_id'].astype(str)

    # In some CSV files the school ID contain spaces, in some it does not
    # Here we remove all spaces from it.
    data['school_admin_id'] = data['school_admin_id'].replace(' ', '', regex=True)

    # For some CSV files the school ID loads as float and after conversion to
    # string contains '.0' at the end, i.e. '1000002.0' should become '1000002'
    data['school_admin_id'] = data['school_admin_id'].replace('\.0', '', regex=True)

    # In some CSV files there are lines not for school, but for "Регионално
    # управление на образованието" or "РУО". Usually these lines are for small
    # number of students.
    #
    # Some of these lines do not have city, municipality. In that cases
    # we use the value from the parent administrative unit.
    for nan_col, value_col in [ ('municipality', 'region'), ('place', 'municipality')]:
        data.loc[data[nan_col].isna(), nan_col] = data[value_col].where(data[nan_col].isna())

    # In the DZI CSV for 2017 There are results for two РУО without school_admin_id
    # Here we fill the school_admin_id, because we know it from other years.
    data.loc[(data['school_admin_id'] == 'nan') & (data['place'] == 'Велико Търново'), 'school_admin_id'] = '3400'
    data.loc[(data['school_admin_id'] == 'nan') & (data['place'] == 'Пазарджик'), 'school_admin_id'] = '1300'

    # unify all variations of Чужбина regions/municipalities
    def _unify_foreign_country(v):
        if 'чужбина' in v.lower():
            return 'Чужбина'
        else:
            return v

    data['region'] = data['region'].apply(_unify_foreign_country)
    data['region'] = data['region'].str.title()

    data['municipality'] = data['municipality'].apply(_unify_foreign_country)
    data['municipality'] = data['municipality'].str.title()


    def _get_pretty_place(value: str) -> str:
        """
        Formats cities and villages in standard way.
        TODO: Some places do not contain `гр.` and `с.` prefixes, as result
        in the database we have `гр. София` and `София` records.
        """
        if not value:
            return value

        # There are values like ГР.СОФИЯ,КВ.ГОРНА БАНЯ
        # We care only for the city part
        if ',' in value:
            value = value.split(',')[0]

        def _upper_first(s: str) -> str:
            if not s:
                return s

            s = s.strip()
            return s[0].upper() + s[1:].lower()

        try:
            if '.' in value:
                prefix, name = value.split('.')
                return f'{prefix.strip().lower()}. {_upper_first(name)}'
            else:
                return _upper_first(value.strip())
        except:
            logger.error('Failed to make pretty place from value %s', value)
            raise

    data['place'] = data['place'].apply(_get_pretty_place)

    # Convert people columns to int
    people_cols = [c for c in data.columns if is_people_column(c)]
    for c in people_cols:
        logger.verbose_info('converting to int people column %s', c)
        data[c] = data[c].fillna(-1).astype('int32')


    # Convert score columns to float
    score_cols = [c for c in data.columns if is_score_column(c)]
    for c in score_cols:
        logger.verbose_info('converting to float score column %s', c)
        fixed = data[c].replace(',', '.', regex=True)
        # dzi-2022 contains one cell with value '('
        fixed = fixed.replace('(',None)
        fixed = fixed.astype(float)
        data[c] = fixed


    # In NVO 4th grade CSV files the subject columns (people and score) are
    # not paired by subject.
    # Here we pair them.
    new_cols = []
    subj_cols = []
    for c in data.columns:
        if is_subject_column(c):
            subj_cols.append(c)
        else:
            new_cols.append(c)

    logger.verbose_info('subject columns before sorting: %s', subj_cols)
    subj_cols = sorted(subj_cols)
    logger.verbose_info('subject columns after  sorting: %s', subj_cols)

    for subj_to_remove in SUBJECTS_TO_REMOVE:
        subj_cols = [s for s in subj_cols if not is_particular_subject_column(s, subj_to_remove)]
    logger.verbose_info('subject columns after removing: %s', subj_cols)

    new_cols = [*new_cols, *subj_cols]

    data = data.loc[:, new_cols]

    # Now we'll re-map subject abbreviations to IDs from Subject table
    # The subject abbreviations are lowercased. The keys in map below loaded
    # with load_subject_abbr_map are also lowercased.
    #
    # The loop below:
    # 1. Builds a dictionary with column new->old names.
    # 2. Raise an exception in case unknown subject is found.
    logger.verbose_info('Columns before subject remapping: %s', data.columns)

    renamings_map = {}
    for c in data.columns:
        if is_subject_column(c):
            subject_abbr, attribute = c.split(' ')
            subject_item = subject_mapping.get(subject_abbr)
            if not subject_item:
                raise ValueError('Cannot find subject for abbreviation %s.', subject_abbr)

            renamings_map[c] = f'{subject_item.id} {attribute}'

    logger.verbose_info('Column name renaming map: %s', renamings_map)
    data = data.rename(columns=renamings_map)
    logger.verbose_info('Columns after  subject remapping: %s', data.columns)

    return data


def extract_school_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    From the raw data extracts a DataFrame containing only data about
    schools
    """
    return data.loc[:, ['region', 'municipality', 'place', 'school', 'school_admin_id']]


def extract_scores_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    From the raw data extracts a DataFrame in the form:
    school_admin_id, subject, max_possible_score, people, score

    This means tha for every pair (people, score) it generates a line for
    the corresponding school.
    """
    subject_cols = [c for c in data.columns if is_subject_column(c)]
    subject_cols_count = len(subject_cols)
    assert subject_cols_count > 0, 'Subject columns cannot be zero.'
    assert subject_cols_count % 2 == 0, \
        f'Subject column count should be an even number, but it is {subject_cols_count}. Columns are: {subject_cols}'

    cols_to_extract = ['school_admin_id', *subject_cols]

    # This DataFrame contains only school_admin_id and subject columns
    scores : pd.DataFrame = data.loc[:, cols_to_extract]

    subject_count = subject_cols_count // 2

    logger.verbose_info('subject_cols_count -> %d, subject_count -> %d', subject_cols_count, subject_count)

    # The for loop below will generate a DataFrame for each subject.
    # The data frame will be added in this list.
    # At the end this list will be concatenated.
    subject_df = []
    for i in range(subject_count):
        # +1 is added because the scores DataFrame contains school_admin_id
        subject_cols = scores.columns[i*2+1 : i*2+1+2]
        logger.verbose_info('subject_cols -> %s', subject_cols )

        subject_name = subject_cols[0].split(' ')[SBJ_IDX]
        logger.verbose_info('extracted subject_name -> %s', subject_name)
        assert subject_name in subject_cols[1], \
            f'The two columns do not contain the same subject name {subject_cols}'

        subject_name = subject_name.upper()
        logger.verbose_info('subject_name -> %s', subject_name)

        df = scores.loc[:, ['school_admin_id', *subject_cols]]

        # rename the columns to be just 'people' and 'score', in other words
        # we remove the subject name from the column names
        renaming_cols = { c: c.split(' ')[ATTR_IDX] for c in subject_cols }
        df = df.rename(columns=renaming_cols)

        # insert the subject in the dataframe
        df.insert(1, 'subject', subject_name)

        # infer and insert the max possible score
        max_possible_score = infer_max_possible_nvo_score(df)
        df.insert(1, 'max_possible_score', max_possible_score)

        # we are ready
        subject_df.append(df)

    # concat all subject data frames in one, sort by school_admin_id
    result = pd.concat(subject_df, ignore_index=True)
    result = result[result['score'] > 0]
    result = result.sort_values('school_admin_id')
    result = result.reset_index()

    return result


def main():
    """
    This main function is used only for testing.
    """

    csv_file = sys.argv[1]
    raw_data = load_csv(csv_file)
    raw_data = refine_csv_column_names(raw_data)
    raw_data.seek(0)

    subject_mapping = load_subject_abbr_map()
    refined_data = refine_data(raw_data, subject_mapping)
    print(refined_data.loc[:3])

    schools_data = extract_school_data(refined_data)
    print(schools_data.loc[:3])

    scores_data = extract_scores_data(refined_data)
    print(scores_data)


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
