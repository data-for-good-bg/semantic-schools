#!/usr/bin/env python3

import pandas as pd
import sys
import logging
import os

from io import StringIO


logger = logging.getLogger(__name__)


COLUMN_TRANSLATE = {
    'област': 'region',
    'регион': 'region',
    'община': 'municipality',
    'населено място': 'place',
    'населено  място': 'place',
    'училище': 'school',
    'код по админ': 'school_admin_id',
    'код': 'school_admin_id',
    'явили се': 'people',
    'ср. успех в точки': 'score',
    'mat': 'мат'
}


def translate_column(value: str) -> str:
    value = value.lower()
    for old_v, new_v in COLUMN_TRANSLATE.items():
        value = value.replace(old_v, new_v)

    return value


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
    # the second one is another weird unicode sequence found in a column name
    to_replace = ['\ufeff', '\u00a0']

    result = StringIO()
    with open(file, 'rb') as f:
        for line in f:
            line = line.decode('utf-8-sig')
            for c in to_replace:
                line = line.replace(c, '')
            result.write(line)

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
    #    Example:
    #      "Област","Община","Населено място","Училище","Код по Админ","Явили се","Ср. успех в точки","Явили се","Ср. успех в точки"
    #      "","","","","","БЕЛ","БЕЛ","МАТ","МАТ"
    # 5. NVO 7th grade 2023
    #    There are four lines describing the maximum possible score for
    #    each subject.
    #    The fifth line contains the column names, in this case the subject
    #    names are in this line.
    #    The sixth line contains the column names for umuber of people and
    #    score.
    #    We'll infer the maximum possible score.
    #
    # The common pattern in all cases is the line containing "Област",....
    # We'll skip everything until that line.
    # Then we may or may not handle the next line.
    #
    #
    input.seek(0)

    column_names = None
    for line in input:
        if line.startswith('"Област') or line.startswith('"Регион'):
            column_names = line.strip()
            break

    assert column_names, 'Cannot find line with column names.'

    output = StringIO()

    next_special_line = input.readline()
    if next_special_line.startswith('""'):
        logger.debug('The line after the column names is special, will handle it')
        # we have special line case
        next_special_line = next_special_line.strip()

        new_col_names = []
        for h, s in zip(column_names.split(','), next_special_line.split(',')):
            h = translate_column(h.replace('"', ''))
            s = translate_column(s.replace('"', ''))

            new_header = h if s == '' else h + ' ' + s
            new_col_names.append(new_header)

        new_headers_line = ','.join(new_col_names) + os.linesep
        logger.debug(new_headers_line)

        output.write(new_headers_line)
    else:
        logger.debug('The line after the column names is not special, adding it to the output')


        new_col_names = []
        for c in column_names.split(','):
            new_col_names.append(translate_column(c))

        new_column_names_line = ','.join(new_col_names) + os.linesep
        logger.info('Translated column names: %s', new_column_names_line)

        output.write(new_column_names_line)
        output.write(next_special_line)


    for line in input:
        output.write(line)

    return output


def get_subject_column_names(data: pd.DataFrame) -> list[str]:
    return [
        col
        for col in data.columns
        if 'people' in col or 'score' in col
    ]


def refine_data(csv_data: StringIO) -> pd.DataFrame:
    csv_data.seek(0)
    data = pd.read_csv(csv_data)

    data['school_admin_id'] = data['school_admin_id'].replace(' ', '', regex=True)

    numeric_cols = get_subject_column_names(data)
    for numberic_col in numeric_cols:
        data[numberic_col] = data[numberic_col].replace(',', '.', regex=True)

    return data


def extract_school_data(data: pd.DataFrame) -> pd.DataFrame:
    return data.loc[:, data.columns[:5]]


def extract_scores_data(data: pd.DataFrame) -> pd.DataFrame:
    subject_cols = get_subject_column_names(data)
    cols_to_extract = ['school_admin_id', *subject_cols]

    scores : pd.DataFrame = data.loc[:, cols_to_extract]
    # subtracting 1 for the schoold_admin_id
    numeric_cols_count = len(scores.columns) - 1
    assert numeric_cols_count > 0
    assert numeric_cols_count % 2 == 0

    subject_count = numeric_cols_count // 2

    logger.debug('numeric_cols_count -> %d, subject_count -> %d', numeric_cols_count, subject_count)
    subject_df = []
    for i in range(subject_count):
        subject_cols = scores.columns[i*2+1 : i*2+3]
        logger.debug('subject_cols -> %s', subject_cols )

        subject_name = subject_cols[0].split(' ')[1]
        logger.debug('extracted subject_name -> %s', subject_name)
        assert subject_cols[1].endswith(subject_name)

        subject_name = subject_name.upper()
        logger.debug('subject_name -> %s', subject_name)

        df = scores.loc[:, ['school_admin_id', *subject_cols]]

        renaming_cols = { c: c.split(' ')[0] for c in subject_cols }
        df = df.rename(columns=renaming_cols)

        df.insert(1, 'subject', subject_name)
        subject_df.append(df)


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
