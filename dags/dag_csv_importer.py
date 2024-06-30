import os
import requests
from tempfile import NamedTemporaryFile
from datetime import date

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable


from csv_importer.import_csv import import_file


# We assume this file is placed in a `dags` directory which is next to
# the `csv_importer/venv` directory, containing a venv for our ExternalPythonOperators
PATH_TO_VENV_PYTHON_BINARY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'csv_importer', 'venv', 'bin', 'python'
)



@dag(
    dag_id='educational_data_csv_importer',
    schedule=None,
    start_date=date(2024, 1, 1),
    catchup=False,
    tags=['schools', 'educational', 'nvo', 'dzi'],
    params={
        'csv_to_import_url': Param(
            'https://data.egov.bg/resource/download/a9b1a68e-ecbb-4cff-8822-3d068ba7dc49/csv',
            'URL to the CSV file to import',
        )
    }
)
def educational_data_csv_importer():


    def prepare_env_vars():
        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'


    @task.external_python(
        python=PATH_TO_VENV_PYTHON_BINARY,
        op_args=['{{ params.csv_to_import_url }}']
    )
    def download_csv_file(csv_to_import_url):
        with requests.get(csv_to_import_url, stream=True) as r:
            r.raise_for_status()
            with NamedTemporaryFile(delete_on_close=False, mode='wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)


                return {
                    'csv_file': f.name
                }


    @task.external_python(
        python=PATH_TO_VENV_PYTHON_BINARY,
    )
    def import_csv(csv_file: str):
        prepare_env_vars()
        import_file(csv_file)

    download_csv_file >> import_csv


educational_data_csv_importer()
