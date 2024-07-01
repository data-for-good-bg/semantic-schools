import os
import pendulum
import logging

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable


logger = logging.getLogger(__name__)


@dag(
    dag_id='educational_data_csv_importer',
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
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

    VENVS_ROOT = Variable.get('VENVS_ROOT')
    PATH_TO_VENV_PYTHON_BINARY = os.path.join(VENVS_ROOT, 'eddata_csv_importer', 'bin', 'python3')

    TASK_VIRTUAL_ENV_ARGS = {
        'requirements': ['pandas==2.2.2', 'requests==2.31.0', 'SQLAlchemy==1.4.52', 'alembic==1.13.1', 'psycopg2-binary==2.9.9', 'apache-airflow==2.8.4'],
        'venv_cache_path': VENVS_ROOT,
        'system_site_packages': False
    }

    def prepare_env_vars():
        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'


    @task.virtualenv(**TASK_VIRTUAL_ENV_ARGS)
    def download_csv_file(*, params):
        import requests
        from tempfile import NamedTemporaryFile
        import logging

        logger = logging.getLogger(__name__)

        csv_to_import_url = params['csv_to_import_url']
        logger.info(f'Will download url: {csv_to_import_url}')
        with requests.get(csv_to_import_url, stream=True) as r:
            r.raise_for_status()
            with NamedTemporaryFile(delete=False, mode='wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)


                return f.name


    @task.virtualenv(**TASK_VIRTUAL_ENV_ARGS)
    def import_csv(csv_file: str):
        import os
        from csv_importer.import_csv import import_file
        import logging

        logger = logging.getLogger(__name__)

        prepare_env_vars()
        logger.info(f'Will import file: {csv_file}')
        import_file(csv_file)
        os.unlink(csv_file)

    import_csv(download_csv_file())


educational_data_csv_importer()
