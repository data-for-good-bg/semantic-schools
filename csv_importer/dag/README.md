This readme contains information about how the csv_importer is configured
to work as Airflow DAG and also information about what else has been tried and
did not work.

# Working state as of 2024-07

## Airflow instance details

Everything was done on the Apache Airflow instance on crunch.data-for-good.bg
which is version 2.8.4.

Inside the linux box the Airflow runs on behalf of a user `airflow`, its
state and configuration are stored in `/home/airflow/airflow`,
its database is in the postgres instance running on the same machine.

The DAGs directory is `/home/airflow/airflow/dags`.

In the `/home/airflow/airflow/airflow.cfg` is configured LocalFilesystemBackend
for secrets like this:
```
backend = airflow.secrets.local_filesystem.LocalFilesystemBackend
backend_kwargs = {"variables_file_path": "/home/airflow/airflow/secrets/var.json", "connections_file_path": "/home/airflow/airflow/secrets/conn.json"}
```

This backend allows storing variables and connections inside the configured
files. These variables/connections can be accessed from DAGs via Airflow API
like this:

```
from airflow.models import Variable
....

Variable.get('MY_VARIABLE_NAME')
```

### The VENVS_ROOT variable

In the `/home/airflow/airflow/secrets/var.json` there's one special
variable  `VENVS_ROOT` which points to directory where DAGs virtual environments
will be created.
Below there's more about how this directory is being used.

## dag_csv_importer.py

### Installing the DAG

This is automated through the `csv_importer/bin/install_dag.sh` script.
The script does the following:
* Copies the dag file into the dags directory
* Creates virtual environment for the DAG

In the future we might have special Airflow DAG which will be configured
to execute such installation scripts, each of the in different github repo.

The target directories are passed to the script through env vars.

## The virtual environment for the DAG

The csv_importer module comes with its own requirements.txt file and
pyproject.toml.

The virtual env is created by:
* installing the requirements file
* installing the csv_importer module in editable mode with this command
  `cd <path-to-repo-root>/csv_importer/ && pip install -e .`
  The editable mode enables faster dev-test cycle, because changes made in any
  of the files under `<path-to-repo-root>/csv_importer/` will be _visible_
  immediately in the virtual env.
  In comparison if editable mode is not used, then after each change another
  `pip install .` should be executed.
* __Installing__ apache-airflow in the DAG's virtual env. This is needed,
  because the DAG uses Airflow APIs for accessing variables.

Unfortunately having apache-airflow in the venv comes with undesired consequences,
because apache-airflow comes with huge amount of dependencies, which may
create version conflict with the DAG's dependencies.

Example: one of Airflow dependencies is SQLAlchemy with version 1.4.52.
Originally the csv_importer modules was using SQLAlchemy 2.0.29, but it was
downgraded in order to avoid version conflict.

An attempt to run the DAG with SQLAlchemy 2.0.29 was made, but then the DAG
fails with some initialization error.

## Finding the DAG's venv

The `dag_csv_importer.py` finds its venv by looking for the VENVS_ROOT Airflow
variable, then it works with the assumption the venv dir is named `csv_importer`.
The code looks like this:
```
    VENVS_ROOT = Variable.get('VENVS_ROOT')
    PATH_TO_VENV_PYTHON_BINARY = os.path.join(VENVS_ROOT, 'csv_importer', 'bin', 'python3')
```

Then the `PATH_TO_VENV_PYTHON_BINARY` variable is passed to all tasks decorated
with `@task.external_python`.

## Accessing the postgres where the data should be imported

Currently the DAG uses Airflow variables for obtaining the details about
the postgres database.
The variables for host, database name and user are configured through the
Airflow UI. The password is stored in the `/home/airflow/airflow/secrets/var.json`
(check the mentions of LocalFilesystemBackend above).

The variables are obtained through the Airflow API `Variable.get(...)`.

Remark: In the future it is possible that all variables would be moved into the
var.json or even start using Airflow connection.

## pyproject.toml file

The `csv_importer/pyproject.toml` file is the simplest possible.
When interpreted by `pip install -e .` pip assumes that the build system is
`setuptools`, despite build system is not configured explicitly.
That's the toml file contains `tool.setuptools` section.

# What has been tried and did not work

## Packaged DAG

According to the Airflow documentation a dag can be packaged as ZIP
([doc link](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#packaging-dags)).

This was tried with `@task.external_python` and `@task.virtualenv`
decorators.
In both cases the dag task which was trying to import `csv_importer` was failing
to import it.
(vitali) I gave up on this approach, because it was not obvious why this does
not work.

## Working with @task.virtualenv

This decorator allows passing set of requirements via decorator argument.

In general the decorator works really well, especially when cached venvs are used
(via `venv_cache_path` argument).

NB: In order to make it working one should install `virtualenv` package with `pip`,
and not with `apt`. The `apt` package creates virtual environments with
different directory structure and the `bin` directory is one level deeper
in `local` directory.
