#!/usr/bin/env python3

import pandas as pd
import sys
import logging
import os

from io import StringIO


logger = logging.getLogger(__name__)


COLUMN_TRANSLATE = {
    'област': 'region',
    'община': 'municipality',
    'населено място': 'place',
    'училище': 'school',
    'код по админ': 'school_admin_id',
    'явили се': 'people',
    'ср. успех в точки': 'score'
}


def translate_column(value: str) -> str:
    value = value.lower()
    translated = COLUMN_TRANSLATE.get(value)
    if translated:
        return translated
    else:
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

    result = StringIO()
    with open(file, 'rb') as f:
        for line in f:
            line = line.decode('utf-8-sig')
            line = line.replace('\ufeff', '')
            result.write(line)

    return result


def convert_csv_columns(input: StringIO) -> StringIO:
    # The first line contains column names
    # The second line contains subject names in those columns which represent
    # information about subject
    # Example:
    #    "Област","Община","Населено място","Училище","Код по Админ","Явили се","Ср. успех в точки","Явили се","Ср. успех в точки"
    #    "","","","","","БЕЛ","БЕЛ","МАТ","МАТ"

    input.seek(0)
    column_names = input.readline().strip()
    subjects = input.readline().strip()

    new_headers = []
    for h, s in zip(column_names.split(','), subjects.split(',')):
        h = translate_column(h.replace('"', ''))
        s = translate_column(s.replace('"', ''))

        new_header = h if s == '' else h + ' ' + s
        new_headers.append(new_header)

    new_headers_line = ','.join(new_headers) + os.linesep
    logger.debug(new_headers_line)

    output = StringIO()
    output.write(new_headers_line)
    for line in input:
        output.write(line)

    return output


def refine_data(csv_data: StringIO) -> pd.DataFrame:
    csv_data.seek(0)
    data = pd.read_csv(csv_data)

    data['school_admin_id'] = data['school_admin_id'].replace(' ', '', regex=True)

    numeric_cols = [col for col in data.columns if 'people' in col or 'score' in col]
    for numberic_col in numeric_cols:
        data[numberic_col] = data[numberic_col].replace(',', '.', regex=True)

    return data


def extract_school_data(data: pd.DataFrame) -> pd.DataFrame:
    return data.loc[:, data.columns[:5]]


def extract_scores_data(data: pd.DataFrame) -> pd.DataFrame:
    scores : pd.DataFrame = data.loc[:, data.columns[4:]]
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
    raw_data = convert_csv_columns(raw_data)
    raw_data.seek(0)
    # for l in raw_data:
    #     print(l.strip())


    refined_data = refine_data(raw_data)
    # print(refined_data.loc[:, ['school_admin_id']])

    # schools_data = extract_school_data(refined_data)
    # print(schools_data)

    scores_data = extract_scores_data(refined_data)
    print(scores_data)


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
