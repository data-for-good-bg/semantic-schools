#!/usr/bin/env python3

"""
A tool for generating airflow cli commands for triggerning DAGs executions.
This is helpful when all the CSV data needs to be re-imported.
"""

import json
import argparse
import os
import re


DAGS = {
    'nvo': 'educational_data_import_nvo_csv',
    'dzi': 'educational_data_import_dzi_csv'
}


def get_dzi_dag_params(year: int, url: str, dry_run: bool):
    return {
        'csv_to_import_url': url,
        'year': year,
        'dry_run': dry_run
    }


def get_nvo_dag_params(year: int, grade: int, url: str, dry_run: bool):
    return {
        'csv_to_import_url': url,
        'year': year,
        'grade': str(grade),
        'dry_run': dry_run
    }


def get_airflow_trigger_command(examination_type: str, year: int, grade: int, resource_id: str, dry_run: bool) -> str:
    dag_id = DAGS[examination_type]
    url = f'https://data.egov.bg/resource/download/{resource_id}/csv'
    if examination_type == 'dzi':
        params = get_dzi_dag_params(year, url, dry_run)
    else:
        params = get_nvo_dag_params(year, grade, url, dry_run)

    params_str = json.dumps(params)

    return f"airflow dags trigger {dag_id} --conf '{params_str}'"


def get_app_py_command(filepath: str, examination_type: str, year: int, grade: int, dry_run: bool, verbose: bool) -> str:
    if examination_type == 'dzi':
        import_cmd = 'import-dzi'
        grade_param = ''
    else:
        import_cmd = 'import-nvo'
        grade_param = f' --grade {grade}'


    dry_run_param = '' if not dry_run else ' -n'
    verbose_param = '' if not verbose else ' -v'

    return f'./app.py {import_cmd} --csv {filepath} --year {year}{grade_param}{dry_run_param}{verbose_param}'


TRUE_VALUES = {'true', 't', 'yes', 'y', '1'}
FALSE_VALUES = {'false', 'f', 'no', 'n', '0'}


def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in TRUE_VALUES:
        return True
    elif value.lower() in FALSE_VALUES:
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_args():
    parser = argparse.ArgumentParser(description='Generates airflow or app.py cli commands for importing data.')

    subparsers = parser.add_subparsers(dest='command', required=True, help='Sub-commands')

    airflow = subparsers.add_parser('airflow', help='Generates commands for airflow CLI')

    # Argument for the CSV file
    airflow.add_argument('csv_file', type=str, help='Path to the "new_sources.csv" or similar file.')

    # Argument for the dry-run flag
    airflow.add_argument('--dry-run-value', type=str2bool,
                        help=('Value for the dry_run argument of the DAGs. '
                              f'Possible values are: {TRUE_VALUES}\n{FALSE_VALUES}'))


    app_py = subparsers.add_parser('app_py', help='Generates commands for app.py')
    app_py.add_argument('--local-csv-dir', type=str, help='Path to the directory containing CSV files')
    app_py.add_argument('--dry-run-value', type=str2bool,
                        help=('Value for the dry_run argument. '
                              f'Possible values are: {TRUE_VALUES}\n{FALSE_VALUES}'))
    app_py.add_argument('--verbose-value', type=str2bool,
                        help=('Value for the verbose argument. '
                              f'Possible values are: {TRUE_VALUES}\n{FALSE_VALUES}'))


    return parser.parse_args()


def generate_for_airflow(args):
    with open(args.csv_file, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            details, resource_id = line.split(',')
            if details.startswith('dzi'):
                etype, year = details.split('-')
                grade = 12
            else:
                etype, grade, year = details.split('-')

            print(get_airflow_trigger_command(etype, int(year), int(grade), resource_id, args.dry_run_value))


def generate_for_app_py(args):
    dzi_re = 'dzi-([0-9]{4})-.*.csv'
    nvo_re = 'nvo-([0-9]+)-([0-9]{4})-.*.csv'
    for item in os.listdir(args.local_csv_dir):
        filepath = os.path.join(args.local_csv_dir, item)

        dzi_m = re.match(dzi_re, item)
        if dzi_m:
            print(get_app_py_command(filepath, 'dzi', dzi_m.group(1), 12, args.dry_run_value, args.verbose_value))
        else:
            nvo_m = re.match(nvo_re, item)
            if nvo_m:
                print(get_app_py_command(filepath, 'nvo', nvo_m.group(2), nvo_m.group(1), args.dry_run_value, args.verbose_value))



def main():
    args = parse_args()
    print(f'args: {args}')

    if args.command == 'airflow':
        generate_for_airflow(args)
    else:
        generate_for_app_py(args)


if __name__ == '__main__':
    main()
