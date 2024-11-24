#!/usr/bin/env python3

"""
This app can be used for importing NVO or DZI CSV files, also to do some
management of the DB.
"""

import logging
import sys
import os
import argparse

from csv_importer.import_csv import import_file
from csv_importer.runtime import enable_verbose_logging, enable_dry_run
from csv_importer.db_manage import list_examinations, delete_examination, init_db
from csv_importer.db import DEFAULT_DB_URL
from csv_importer.wikidata import extract_wikidata


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

    # Subparser for import-dzi
    parser_dzi = subparsers.add_parser('import-dzi', help='Import DZI data')
    parser_dzi.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
    parser_dzi.add_argument('--year', type=int, required=True, help='Year')
    parser_dzi.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_dzi.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')

    # Subparser for import-nvo
    parser_nvo = subparsers.add_parser('import-nvo', help='Import NVO data')
    parser_nvo.add_argument('--csv', type=str, required=True, help='Path to the CSV file')
    parser_nvo.add_argument('--year', type=int, required=True, help='Year')
    parser_nvo.add_argument('--grade', type=int, required=True, help='Grade')
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
    parser_extract_wiki_data = subparsers.add_parser('extract-wikidata', help='Extracts data from wikidata')
    # parser_extract_wiki_data.add_argument('--id', type=str, required=True, help='ID of the examination to be delete')
    parser_extract_wiki_data.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser_extract_wiki_data.add_argument('-n', '--dry-run', action='store_true', help='Perform a dry run without making changes')


    args = parser.parse_args()
    return args


def main():

    args = parse_args()
    print(f'args: {args}', file=sys.stderr)

    if args.verbose:
        enable_verbose_logging()

    if args.dry_run:
        enable_dry_run()

    if args.command == 'import-dzi':
        import_file(args.csv, 'dzi', 12, args.year)
    elif args.command == 'import-nvo':
        import_file(args.csv, 'nvo', args.grade, args.year)
    elif args.command == 'init-db':
        init_db()
    elif args.command == 'list-examinations':
        list_examinations()
    elif args.command == 'delete-examination':
        delete_examination(args.id)
    elif args.command == 'extract-wikidata':
        extract_wikidata()
    else:
        raise RuntimeError(f'Unsupported command: {args.command}')

if __name__ == '__main__':
    log_level = logging.DEBUG if os.environ.get('DEBUG', 'no') == 'yes' else logging.INFO
    logging.basicConfig(level=log_level)
    main()
