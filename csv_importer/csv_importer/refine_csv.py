#!/usr/bin/env python3

"""
This script provides functoins for working with NVO and DZI CSV files provided
by data.egov.bg.

It is supposed that these functions will be used by another script which
will convert/import the data somewhere.

It can be used as a standalone app by passing one CSV file to it. This is
dev use case - it calls all main functions on the provided CSV file.

"""

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
    'код по неиспуо': 'school_admin_id',
    'код': 'school_admin_id',
    'mat': 'мат',
    '\)з': ')-з', # there's one special case in dzi-2022
    ' \(мах 100 т\)': '', #nov-4-2018
    '\(пп\)': '', # dzi-2022
    '\(ооп\)': '', # dzi-2022
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

# Subject columns in the data frames are structured like this
# 'БЕЛ people' and 'БЕЛ score'. The two constants are the indexes of
# subject name and column name in such columns.
SBJ_IDX = 0
CN_IDX = 1


def refine_original_col_name(value: str) -> str:
    """
    This function changes original column names.
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
    logger.debug('max score value calculated is: %s', max_score)

    if max_score <= 6.00:
        return 6.00

    if max_score <= 65.00:
        return 65.00

    return 100.00


def load_csv(file: str) -> StringIO:
    # using 'utf-8-sig' encoding to handle the BOM csv files provided
    # by data.egov.bg
    # Some of the CSV files contain the BOM mark not only at the beginning
    # of the file, but also inside the first value on the first line.
    # That's why below we replace the sequence '\ufeff' everywhere.
    # https://en.wikipedia.org/wiki/Byte_order_mark
    # https://docs.python.org/3/howto/unicode.html
    # https://stackoverflow.com/questions/13590749/reading-unicode-file-data-with-bom-chars-in-python

    # The first unicode sequence is the BOM mark,
    # The second one is another weird unicode sequence found in a column name.
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

    Rest of the CSV files are in a form which this function (and tool) supports.

    Here are more details about the supported formats and their variations:

    1. All supported formats contain a line with column names which starts with
    column Област or in one case Регион.

    Examples:
    * nvo-4-2019
        "Област","Община","Населено място","Код","Училище","Явили се МАТ","Явили се БЕЛ","Явили се ЧО","Явили се ЧП","Ср. успех в точки МАТ","Ср. успех в точки БЕЛ","Ср. успех в точки ЧО","Ср. успех в точки ЧП"
    * nvo-4-2022
        "Област","Община","Населено място","Училище","Код по АДМИН","БЕЛ Явили се","БЕЛ Ср. успех в точки","МАТ Явили се","МАТ  Ср. успех в точки"

    2. In some cases this line is preceeded by several additional lines
    which describe what the file is about. These lines are not well structured
    and this function ignores them.
    There's loop below which skips all lines before the line starting with
    'Област'.

    Examples: nvo-7-2018

    3. In scome case the line with column names is followed by one or two
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

    NB: In dzi-2023 example there is colimn "БЕЛ(ПП)" followed by empty column,
    then "Мат(ПП)" and again empty column. The empty columns are filled
    from their preceeding column.

    ---

    In all three variations the function constructs a single line
    with column names.
    After that this line is partially translated to english. All variations
    of 'Явили се' are translated to the term 'people', all variations of
    'Среден успех' are translated to 'score.
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

    At the end this function retruns the input StringIO changed to contain
    only one line with column names. This way it is ready to be imported
    by  Pandas.

    """

    input.seek(0)

    # This loop finds the line with the original column names and
    # also the lines which contain additional column options
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
    # the name of the previous column.
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

        # merge new_col_names with the current options and produce
        # list with the merged values
        ex_col_names = []
        for col_name, option in zip(new_col_names, options):
            # strip is important for the empty options
            new_col_name = f'{col_name} {option}'.strip()
            ex_col_names.append(new_col_name)
        new_col_names = ex_col_names

        logger.debug('options: %s', options)
        logger.debug('new_col_names: %s', new_col_names)

    # translate  columns
    for i in range(len(new_col_names)):
        new_col_names[i] = refine_original_col_name(new_col_names[i])
    logger.debug('new_col_names: %s', new_col_names)

    # organize all subject column names to contain subject at the beginning
    new_col_names = order_attr_in_subject_column_names(new_col_names)
    logger.debug('new_col_names: %s', new_col_names)

    # construct the new column names line
    new_column_names_lines = ','.join(new_col_names) + os.linesep
    logger.debug('new_column_names_lines: %s', new_column_names_lines)

    output.write(new_column_names_lines)

    # copy add all other lines into the result
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

    # convert school id column to str
    data['school_admin_id'] = data['school_admin_id'].astype(str)

    # dzi-2018 contains two rows for РУО, those rows do not have place, that's
    # why we delete these rows
    data = data[data['place'].isna() == False]

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


    def _get_prety_place(value: str) -> str:
        """
        Formats cities and villages in standard way.
        """
        if not value:
            return value

        try:
            if '.' in value:
                prefix, name = value.split('.')
                return f'{prefix.strip().lower()}. {name.strip().title()}'
            else:
                    return value.strip().title()
        except:
            logger.error('Failed to make prety place from value %s', value)
            raise

    data['place'] = data['place'].apply(_get_prety_place)


    # Conver people columns to int
    people_cols = [c for c in data.columns if is_people_column(c)]
    for c in people_cols:
        logger.debug('converting to int people column %s', c)
        data[c] = data[c].fillna(-1).astype('int32')


    # Conver score columns to float
    score_cols = [c for c in data.columns if is_score_column(c)]
    for c in score_cols:
        logger.debug('converting to float score column %s', c)
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
    subject_cols = [c for c in data.columns if is_subject_column(c)]
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
    result = pd.concat(subject_df, ignore_index=True)
    result = result[result['score'] > 0]
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
    print(scores_data)


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
