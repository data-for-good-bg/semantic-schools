#!/usr/bin/env python3

import pandas as pd
import sys
import logging
import os
import re

from io import StringIO


logger = logging.getLogger(__name__)


# List of regular expressions which will be translated no matter where
# in the column name are found
COL_RE_TRANSLATION = {
    'област': 'region',
    'регион': 'region',
    'община': 'municipality',
    'населено място': 'place',
    'населено  място': 'place',
    'училище': 'school',
    'код по админ': 'school_admin_id',
    'код': 'school_admin_id',
    'mat': 'мат',
    '\)з': ')-з', # there's one special case in dzi-2022
    ' \(мах 100 т\)': '', #nov-4-2018
    '\(пп\)': '', # dzi-2022
    '\(ооп\) ': '', # dzi-2022
    ' з': '-з',
    ' (b1-|b1.1-|b2-)з': r'-\1з',

}

# List of regular expressions which will be translated only if they
# are found at the beginning or at the end of the column name
COL_RE_TRANSLATION_SPECIAL_POSITIONS = {
    'явили се': 'people',
    'ср\. успех в точки': 'score',
    'ср\.успех': 'score',
    'ср\.усп\.': 'score',
    'ср\.усп': 'score',

    'бр\.': 'people',
    'брой': 'people',
}


SBJ_IDX = 0
CN_IDX = 1


def refine_original_col_name(value: str) -> str:
    """
    This function changes original (or raw) column names.
    * translates known texts from Bulgarian to English
    * lowers all letters
    * removes redundant information or characters
    """

    logger.debug('value %s', value)

    value = value.replace('"', '')
    value = value.lower()
    logger.debug('value %s', value)

    while '  ' in value:
        value = value.replace('  ', ' ')
    logger.debug('value %s', value)


    for regex, repl in COL_RE_TRANSLATION.items():
        value = re.sub(regex, repl, value)
        value = value.strip()
    logger.debug('value %s', value)

    for base_regex, repl in COL_RE_TRANSLATION_SPECIAL_POSITIONS.items():
        value = re.sub(f'^{base_regex}', repl, value)
        value = re.sub(f'{base_regex}$', repl, value)
        value = value.strip()
    logger.debug('value %s', value)

    # sometimes there's missing space between the subject name and
    # the score
    if 'score' in value and not value.startswith('score') and ' score' not in value:
        value = value.replace('score', ' score')
    logger.debug('value %s', value)

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


def is_subject_column(col_name: str) -> bool:
    return col_name.endswith(' people') or col_name.endswith(' score')


def get_subject_column_names(data: pd.DataFrame) -> list[str]:
    return [
        col
        for col in data.columns
        if is_subject_column(col)
    ]


def infer_max_possible_nvo_score(data: pd.DataFrame) -> float:
    """
    Infers the max possible score for NVO based on the maximum score
    found in the data frame.

    The maximum possible score:
    * was 65 points for several years
    * after that the max possible score is 100 points

    """

    assert 'score' in data.columns, \
        'The data frame should contain score column in order to infer the max possible score.'
    max_score = data['score'].max()

    if max_score <= 65.00:
        return 65.00
    else:
        return 100.00


def load_csv(file: str) -> StringIO:
    # using 'utf-8-sig' encoding to handle the BOM csv files provided
    # by data.egov.bg
    # Some of the CSV files contain the BOM mark not only at the beginning
    # of the file, also inside the first value on the first line.
    # That's why below we replace the sequence '\ufeff' everywhere (this
    # is the three byte representation of the BOM mark U+FEFF)
    # https://en.wikipedia.org/wiki/Byte_order_mark
    # https://docs.python.org/3/howto/unicode.html
    # https://stackoverflow.com/questions/13590749/reading-unicode-file-data-with-bom-chars-in-python

    # The first unicode sequence is the BOM mark,
    # The second one is another weird unicode sequence found in a column name
    # The third item is because one of the files contains: "<BOM>""Област"""
    #   So the <BOM> will be replaced, then we handle the trippled quotes
    #   It is handled by this special way, because it is not good idea to handle
    #   trippled quotes in the whole file.
    to_replace = {
        '\ufeff': '',
        '\u00a0': '',
        '"""Област"""': '"Област"'
    }

    result = StringIO()
    with open(file, 'rb') as f:
        for line in f:
            line = line.decode('utf-8-sig')
            for old_v, new_v in to_replace.items():
                line = line.replace(old_v, new_v)

            result.write(line)

    return result


def fill_empty_cells_from_previous(input: list[str]) -> list[str]:
    """
    Takes a list as input and returns another where empty elements
    from the previous element.

    ['','','a','','b',''] -> ['', '', 'a', 'a', 'b','b']

    """
    if not input:
        return input

    result = [input[0]]
    for i in range(1, len(input)):
        if input[i] == '':
            result.append(input[i-1])
        else:
            result.append(input[i])
    return result


def refine_csv_column_names(input: StringIO) -> StringIO:
    # The NVO 7th grade CSV files first several lines describe the structure
    # of the file, but there are variations:
    # 1. NVO 7th grade 2016 - not handled yet
    # 2. NVO 7th grade 2018
    #    The first three lines describe the maximum possible score for the two
    #    subjects. These three lines are skipped, the maximum possible score
    #    will be inferred.
    # 3. NVO 7th grade 2019, 2020, 2022
    #    There first line contains the column names, there are no any
    #    special lines
    # 4. NVO 7th grade 2021
    #    The first line contains the column names, the second line contains
    #    abbriviations of the subjects in the columns where values for the
    #    corresponding subjects are stored
    # 5. NVO 7th grade 2023
    #    There are four lines describing the maximum possible score for
    #    each subject.
    #    The fifth line contains the column names, in this case the subject
    #    names are in this line.
    #    The sixth line contains the column names for umuber of people and
    #    score.
    #    We'll infer the maximum possible score.
    #
    #
    # NB1
    # The common pattern in all cases is the line containing "Област",....
    # We'll skip everything until that line.
    # Then we may or may not handle the next line.
    #
    # NB2
    # In some files column names are paired by subject, i.e. we have
    # 'Явили се subj-x','Ср. успех в точки subj-x','Явили се subj-y','Ср. успех в точки subj-y'
    # In other files that's not true.
    # That's why this function also changes the column names to contain
    # the subject in at the benning of the name. After the columns are translated
    # and re-organized they will look like this.
    # 'subj-x people','subj-y people','subj-x score','subj-y score'
    # Later the whole dataframe will be organized in such way that the
    # columns are paired by subject
    #

    input.seek(0)

    # This loop finds the line with the original column names and
    # also the lines which
    column_names_line = None
    column_option_lines = []
    for line in input:
        if column_names_line is None:
            if line.startswith('"Област') or line.startswith('"Регион'):
                column_names_line = line.strip()
        else:
            if line.startswith('""'):
                column_option_lines.append(line.strip())
            else:
                break

    assert column_names_line, 'Cannot find line with column names.'
    logger.debug('column_names_line: %s', column_names_line)

    output = StringIO()

    # get the original column lines, remove the double quotes
    new_col_names = [
        c.replace('"', '')
        for c in column_names_line.split(',')
    ]
    logger.debug('new_col_names: %s', new_col_names)

    # In some files there are columns without name. These columns take
    # the name of the previous column (this is usually subject name).
    new_col_names = fill_empty_cells_from_previous(new_col_names)
    logger.debug('new_col_names: %s', new_col_names)

    # Merge the new column names with the values of the lines with column
    # options
    for option_line in column_option_lines:
        options = [
            c.replace('"', '')
            for c in option_line.split(',')
        ]
        logger.debug('options: %s', options)
        options = fill_empty_cells_from_previous(options)
        logger.debug('options: %s', options)
        ex_col_names = []
        for col_name, option in zip(new_col_names, options):
            new_col_name = f'{col_name} {option}'.strip()
            ex_col_names.append(new_col_name)
        new_col_names = ex_col_names

        logger.debug('options: %s', options)
        logger.debug('new_col_names: %s', new_col_names)


    for i in range(len(new_col_names)):
        new_col_names[i] = refine_original_col_name(new_col_names[i])
    logger.debug('new_col_names: %s', new_col_names)

    new_col_names = order_attr_in_subject_column_names(new_col_names)
    logger.debug('new_col_names: %s', new_col_names)

    new_column_names_lines = ','.join(new_col_names) + os.linesep
    logger.debug('new_column_names_lines: %s', new_column_names_lines)

    output.write(new_column_names_lines)

    # add all other lines
    for line in input:
        output.write(line)

    return output


def refine_data(csv_data: StringIO) -> pd.DataFrame:
    """
    This function loads a CSV file into pandas DataFrame and
    does some basic refinining actions on the data.
    """

    csv_data.seek(0)
    data = pd.read_csv(csv_data)

    # In some CSV files the schoold ID contain spaces, in some it does not
    # Here we remove all spaces from it.
    data['school_admin_id'] = data['school_admin_id'].replace(' ', '', regex=True)

    # The score column in CSV files is with comman and pandas imports them
    # as string, not as float
    # Here we convert these columns to float type
    subject_cols = get_subject_column_names(data)
    for subject_col in subject_cols:
        logger.debug('converting to float column %s', subject_col)
        fixed = data[subject_col].replace(',', '.', regex=True)
        # dzi-2022 contains one cell with value '('
        fixed = fixed.replace('(',None)
        fixed = fixed.astype(float)
        data[subject_col] = fixed


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

    logger.debug('subject columns before sorting: %s', subj_cols)
    subj_cols = sorted(subj_cols)
    logger.debug('subject columns after  sorting: %s', subj_cols)

    new_cols = [*new_cols, *subj_cols]

    data = data.loc[:, new_cols]

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
    subject_cols = get_subject_column_names(data)
    subject_cols_count = len(subject_cols)
    assert subject_cols_count > 0, 'Subject columns cannot be zero.'
    assert subject_cols_count % 2 == 0, \
        f'Subject column count should be an even number, but it is {subject_cols_count}. Columns are: {subject_cols}'

    cols_to_extract = ['school_admin_id', *subject_cols]

    # This DataFrame contains only school_admin_id and subject columns
    scores : pd.DataFrame = data.loc[:, cols_to_extract]

    subject_count = subject_cols_count // 2

    logger.debug('subject_cols_count -> %d, subject_count -> %d', subject_cols_count, subject_count)

    # The for loop below will generate a DataFrame for each subject.
    # The data frame will be added in this list.
    # At the end this list will be concatenated.
    subject_df = []
    for i in range(subject_count):
        # +1 is added because the scores DataFrame contains school_admin_id
        subject_cols = scores.columns[i*2+1 : i*2+1+2]
        logger.debug('subject_cols -> %s', subject_cols )

        subject_name = subject_cols[0].split(' ')[SBJ_IDX]
        logger.debug('extracted subject_name -> %s', subject_name)
        assert subject_name in subject_cols[1], \
            f'The two columns do not contain the same subject name {subject_cols}'

        subject_name = subject_name.upper()
        logger.debug('subject_name -> %s', subject_name)

        df = scores.loc[:, ['school_admin_id', *subject_cols]]

        # rename the columns to be just 'people' and 'score', in other words
        # we remove the subject name from the column names
        renaming_cols = { c: c.split(' ')[CN_IDX] for c in subject_cols }
        df = df.rename(columns=renaming_cols)

        # insert the subject in the dataframe
        df.insert(1, 'subject', subject_name)

        # infer and insert the max possible score
        max_possible_score = infer_max_possible_nvo_score(df)
        df.insert(1, 'max_possible_score', max_possible_score)

        # we are ready
        subject_df.append(df)

    # concat all subject data frames in one, sort by school_admin_id
    result = pd.concat(subject_df)
    result = result.sort_values('school_admin_id')
    return result


def main():

    csv_file = sys.argv[1]
    raw_data = load_csv(csv_file)
    raw_data = refine_csv_column_names(raw_data)
    raw_data.seek(0)

    refined_data = refine_data(raw_data)
    print(refined_data.loc[:3])

    schools_data = extract_school_data(refined_data)
    print(schools_data.loc[:3])

    scores_data = extract_scores_data(refined_data)
    print(scores_data.loc[:3])


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
