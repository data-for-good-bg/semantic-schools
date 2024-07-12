#!/usr/bin/env python3

"""
A tool for generating airflow cli commands for triggerning DAGs executions.
This is helpful when all the CSV data needs to be re-imported.
"""

import json
import argparse


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
    parser = argparse.ArgumentParser(description='Generates airflow cli commands for triggering DAGs.')

    # Argument for the CSV file
    parser.add_argument('csv_file', type=str, help='Path to the "new_sources.csv" or similar file.')

    # Argument for the dry-run flag
    parser.add_argument('--dry-run-value', type=str2bool,
                        help=('Value for the dry_run argument of the DAGs. '
                              f'Possible values are: {TRUE_VALUES}\n{FALSE_VALUES}'))

    return parser.parse_args()


def main():
    args = parse_args()
    print(f'args: {args}')


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


if __name__ == '__main__':
    main()
