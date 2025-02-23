#!/usr/bin/env python3

"""
This app can be used for importing NVO or DZI CSV files, also to do some
management of the DB.
"""

import logging
import sys
import os
import argparse

from csv_importer.import_csv import import_file, SUPPORTED_IMPORT_CSV_TYPES
from csv_importer.runtime import enable_verbose_logging, enable_dry_run
from csv_importer.db_manage import list_examinations, delete_examination, init_db
from csv_importer.db import DEFAULT_DB_URL
from csv_importer.wikidata import import_from_wikidata, SUPPORTED_IMPORT_WIKIDATA_TYPES
from csv_importer.import_mon_csv import import_mon_csv


_cli_help=\
f'''
CLI application for importing DZI or NVO CSV data.

The target DB is defined via DB_URL environment variable.
Its default value is: {DEFAULT_DB_URL}
'''

def parse_args():
    parser = argparse.ArgumentParser(
        description=_cli_help,
        formatter_class=argparse.RawTextHelpFormatter
        )

    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-commands')

    default_csv_to_import = SUPPORTED_IMPORT_CSV_TYPES
    help_csv_to_import = f'Specifies what data to be imported from the CSV. By default imports {default_csv_to_import}.'

    default_wikidata_to_import = SUPPORTED_IMPORT_WIKIDATA_TYPES
    help_wikidata_to_import = f'Specifies what data to be imported from the CSV. By default imports {default_wikidata_to_import}.'

    # Subparser for import-dzi
    parser_dzi = subparsers.add_parser('import-dzi', help='Import DZI data')
    parser_dzi.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
    parser_dzi.add_argument('--year', type=int, required=True, help='Year')
    parser_dzi.add_argument('--to-import', type=str, nargs='*', default=default_csv_to_import, help=help_csv_to_import)
    parser_dzi.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_dzi.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for import-nvo
    parser_nvo = subparsers.add_parser('import-nvo', help='Import NVO data')
    parser_nvo.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
    parser_nvo.add_argument('--year', type=int, required=True, help='Year')
    parser_nvo.add_argument('--grade', type=int, required=True, help='Grade')
    parser_nvo.add_argument('--to-import', type=str, nargs='*', default=default_csv_to_import, help=help_csv_to_import)
    parser_nvo.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_nvo.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for init db steps
    parser_init_db = subparsers.add_parser('init-db', help='This command puts initial data in tables like Subject')
    parser_init_db.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_init_db.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for list-examinations
    parser_list_exam = subparsers.add_parser('list-examinations', help='List records from table examinations')
    parser_list_exam.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_list_exam.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for delete-examination
    parser_del_exam = subparsers.add_parser('delete-examination', help='Delete everything related to the specified examination')
    parser_del_exam.add_argument('--id', type=str, required=True, help='ID of the examination to be delete')
    parser_del_exam.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_del_exam.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for extracting data from wikidata
    parser_import_from_wikidata = subparsers.add_parser('import-from-wikidata', help='Imports data from wikidata')
    # parser_extract_wiki_data.add_argument('--id', type=str, required=True, help='ID of the examination to be delete')
    parser_import_from_wikidata.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_import_from_wikidata.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser_import_from_wikidata.add_argument('--to-import', type=str, nargs='*', default=default_wikidata_to_import, help=help_wikidata_to_import)


    # Subparser for import-mon-schools
    parser_import_mon_schools = subparsers.add_parser('import-mon-schools', help='Import MON schools data')
    parser_import_mon_schools.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
    parser_import_mon_schools.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_import_mon_schools.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')


    args = parser.parse_args()
    if 'to_import' in args:
        if args.command == 'import-from-wikidata':
            valid_values = default_wikidata_to_import
        else:
            valid_values = default_csv_to_import
        for item in args.to_import:
            if item not in valid_values:
                raise ValueError(f'`{item}` is not any of the valid --to-import values, the valid values are: {valid_values}.')

    return args


def main():

    args = parse_args()
    print(f'args: {args}', file=sys.stderr)

    if args.verbose:
        enable_verbose_logging()

    if args.dry_run:
        enable_dry_run()

    if args.command == 'import-dzi':
        import_file(args.csv, 'dzi', 12, args.year, args.to_import)
    elif args.command == 'import-nvo':
        import_file(args.csv, 'nvo', args.grade, args.year, args.to_import)
    elif args.command == 'init-db':
        init_db()
    elif args.command == 'list-examinations':
        list_examinations()
    elif args.command == 'delete-examination':
        delete_examination(args.id)
    elif args.command == 'import-from-wikidata':
        import_from_wikidata(args.to_import)
    elif args.command == 'import-mon-schools':
        import_mon_csv(args.csv)
    else:
        raise RuntimeError(f'Unsupported command: {args.command}')

if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
