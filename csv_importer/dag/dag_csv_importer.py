import os
import pendulum
import logging

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable

# from airflow.operators.python import ExternalPythonOperator

logger = logging.getLogger(__name__)


@dag(
    dag_id='educational_data_csv_importer',
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=['schools', 'educational', 'nvo', 'dzi'],
    params={
        'csv_to_import_url': Param(
            default='https://data.egov.bg/resource/download/a9b1a68e-ecbb-4cff-8822-3d068ba7dc49/csv',
            description='URL to the CSV file to import',
        ),
        'examination_type': Param(
            type='string',
            enum=['nvo', 'dzi'],
            description='Suported values are "nvo" and "dzi" (without the quotes).'
        ),
        'grade': Param(
            type='integer',
            description='Grade (class) of the imported data. Example values are: 4, 7, 10, 12.'
        ),
        'year': Param(
            type='integer',
            description='Year of the data being imported.'
        )
    }
)
def educational_data_csv_importer():

    VENVS_ROOT = Variable.get('VENVS_ROOT')
    PATH_TO_VENV_PYTHON_BINARY = os.path.join(VENVS_ROOT, 'csv_importer', 'bin', 'python3')

    TASK_VIRTUAL_ENV_ARGS = {
        'python': PATH_TO_VENV_PYTHON_BINARY
    }

    @task.external_python(**TASK_VIRTUAL_ENV_ARGS)
    def download_csv_file(params):
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

    @task.external_python(**TASK_VIRTUAL_ENV_ARGS)
    def import_csv(csv_file, params):
        import os
        from csv_importer.import_csv import import_file
        from airflow.models import Variable
        import logging

        logger = logging.getLogger(__name__)

        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'

        logger.info(f'Will import file: {csv_file}')
        import_file(csv_file, params['examination_type'], params['grade'], params['year'])
        os.unlink(csv_file)

    # download_task = ExternalPythonOperator(
    #     task_id='download_csv_file',
    #     python_callable=download_csv_file,
    #     op_kwargs={'csv_to_import_url': '{{ params.csv_to_import_url }}'},
    #     **TASK_VIRTUAL_ENV_ARGS
    # )

    # import_csv_task = ExternalPythonOperator(
    #     task_id='import_csv',
    #     python_callable=import_csv,
    #     op_kwargs={'task_instance': '{{ task_instance }}'},
    #     **TASK_VIRTUAL_ENV_ARGS
    # )

    # download_task >> import_csv_task
    import_csv(download_csv_file())


educational_data_csv_importer()
