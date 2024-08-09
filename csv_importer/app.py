#!/usr/bin/env python3

"""
This app can be used for importing NVO or DZI CSV files.

Currently it does not have fancy argument parsing, one should pass the
arguments in the following order:

1. path to the CSV file to be importer
2. the type of data being imported, supported values are 'nvo' and 'dzi'
3. The grade, example values are 4, 7, 10, 12...
4. The year, example values are 2022, 2023, 2024...
"""

import logging
import sys
import os

from csv_importer.import_csv import import_file


def main():
    csv_file = sys.argv[1]
    examination_type = sys.argv[2]
    grade = int(sys.argv[3])
    year = int(sys.argv[4])
    import_file(csv_file, examination_type, grade, year)


if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
