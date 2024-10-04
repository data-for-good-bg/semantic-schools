import os
import pendulum
import logging

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable


logger = logging.getLogger(__name__)


@dag(
    dag_id='educational_data_import_dzi_csv',
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=['schools', 'educational', 'dzi', 'maturi', 'matura', 'import', 'csv'],
    max_active_runs=1,
    params={
        'csv_to_import_url': Param(
            default='',
            description_md='''
            URL to the CSV file to import.
            At this [data.egov.bg page](https://data.egov.bg/data/view/066b4b04-d81d-444e-a61c-8ca0516079e4)
            there is a list of resources, one per school year.

            Each of the resource pages contains URL to the CSV file with the
            DZI data for the selected school year.

            Pick a CSV URL from such resource page and provide it here.
            ''',
        ),
        'year': Param(
            type='integer',
            description='Year of the data being imported.'
        ),
        'dry_run': Param(
            type='boolean',
            default=False,
            description='When this parameter is True the DAG will only log, it will not change the database.'
        )
    }
)
def educational_data_import_dzi_csv():

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
        from csv_importer.runtime import enable_dry_run, enable_verbose_logging
        from airflow.models import Variable
        import logging

        logger = logging.getLogger(__name__)

        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'

        if params['dry_run'] == True:
            logger.info('Will do dry-run execution')
            enable_dry_run()

        enable_verbose_logging()

        logger.info(f'Will import file: {csv_file}')
        import_file(csv_file, 'dzi', 12, params['year'])
        os.unlink(csv_file)

    import_csv(download_csv_file())


@dag(
    dag_id='educational_data_import_nvo_csv',
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=['schools', 'educational', 'nvo', 'import', 'csv'],
    max_active_runs=1,
    params={
        'csv_to_import_url': Param(
            default='',
            description_md='''
            URL to the CSV file to import.

            Use one of the following pages, each containing resources for each year:
             * [NVO 4th grade](https://data.egov.bg/organisation/dataset/5613e75f-2b1b-4244-9f54-b27580a91dfb)
             * [NVO 7th grade](https://data.egov.bg/organisation/dataset/b56288b6-25aa-4049-9aa6-de2cd4cdabf8)
             * [NVO 10th grade](https://data.egov.bg/data/view/2f801b2f-d4cb-4ddb-a23d-3e372339c80f)

            Each of the resource pages contains URL to the CSV file with the
            NVO data for the selected school year.

            Pick a CSV URL from such resource page and provide it here.
            ''',
        ),
        'year': Param(
            type='integer',
            description='Year of the data being imported.'
        ),
        'grade': Param(
            type='string',
            description='Grade of the data being imported.',
            enum=['4', '7', '10'],
        ),
        'dry_run': Param(
            type='boolean',
            default=False,
            description='When this parameter is True the DAG will only log, it will not change the database.'
        )
    }
)
def educational_data_import_nvo_csv():

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
        from csv_importer.runtime import enable_dry_run, enable_verbose_logging
        from airflow.models import Variable
        import logging

        logger = logging.getLogger(__name__)

        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'

        if params['dry_run'] == True:
            logger.info('Will do dry-run execution')
            enable_dry_run()

        enable_verbose_logging()

        grade = int(params['grade'])

        logger.info(f'Will import file: {csv_file}')
        import_file(csv_file, 'nvo', grade, params['year'])
        os.unlink(csv_file)

    import_csv(download_csv_file())


@dag(
    dag_id='educational_data_delete_examination',
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=['schools', 'educational', 'dzi', 'maturi', 'matura'],
    max_active_runs=1,
    params={
        'examination_ids': Param(
            default='',
            description=(
                'Comma separated list of examination_id. The DAG will'
                ' delete the examination record and all examination_score'
                ' records matching the specified ids.'
            )
        ),
        'dry_run': Param(
            type='boolean',
            default=False,
            description='When this parameter is True the DAG will only log, it will not change the database.'
        )
    }
)
def educational_data_delete_examination():
    VENVS_ROOT = Variable.get('VENVS_ROOT')
    PATH_TO_VENV_PYTHON_BINARY = os.path.join(VENVS_ROOT, 'csv_importer', 'bin', 'python3')

    TASK_VIRTUAL_ENV_ARGS = {
        'python': PATH_TO_VENV_PYTHON_BINARY
    }

    @task.external_python(**TASK_VIRTUAL_ENV_ARGS)
    def delete_examination(params):
        import os
        from csv_importer.db_manage import delete_examination
        from csv_importer.runtime import enable_dry_run, enable_verbose_logging
        from airflow.models import Variable
        import logging

        logger = logging.getLogger(__name__)

        db_host = Variable.get('EDDATA_DB_HOST')
        db_name = Variable.get('EDDATA_DB_NAME')
        db_user = Variable.get('EDDATA_DB_USER')
        db_pass = Variable.get('EDDATA_DB_PASS')

        os.environ['DB_URL'] = f'postgresql://{db_user}:{db_pass}@{db_host}/{db_name}'

        if params['dry_run'] == True:
            logger.info('Will do dry-run execution')
            enable_dry_run()

        enable_verbose_logging()

        examination_ids = params['examination_ids']
        examination_ids = examination_ids.split(',')
        for examination_id in examination_ids:
            if examination_id:
                logger.info(f'Will delete examination: {examination_id}')
                delete_examination(examination_id)

    delete_examination()


educational_data_import_dzi_csv()
educational_data_import_nvo_csv()
educational_data_delete_examination()
