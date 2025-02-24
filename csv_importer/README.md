# Intro

This directory contains python code which handles importing NVO and DZI
data provided by egov.data.bg into relational or graph DB.


Organization of the directory:
* ./csv_importer/ directory is a python package.

  Note that from repo root point of view there's ./csv_importer/csv_importer
  directory. The nested `csv_importer` had to be created in order
  to organize it as python package which is installable via `pip install`.
  The `pyproject.toml` (described below) is part of the python package description.

  The key modules are:
  * refine_csv.py - provides functions for loading CSV file and refining
    the data. The result is pandas DataFrame object which could be used
    for importing the data into relational or graph database.

  * import_csv.py - provide function for loading a CSV file and importing
    it into relational database.
  * models.py is the place to describe models which could be used for
    relational and graph databases. An example for such model is the Subject
    (учебен предмет) and all of instances.
  * db_models.py is the module where are defined the SQLAlchemy models
    for working with relational DBs
  * The db.py, db_actions.py and db_manage.py modules provide functions for
    working with relational database, currently postgres. They also use SQLAlchemy library.
  * runtime.py defines classes and functions related to given execution of
    the import application - logging, dry-run, etc.
  * ./alembic directory contains the Alembic configuration and DB migrations.

* ./pyproject.toml - This pyproject file describes the `./csv_importer` package.
  It is the simplest possible pyproject file which enables installing the
  package in editable mode.
  There's more information on the topic in the ./dag/README.MD.

* ./requirements.txt - the set of python dependencies of the ./csv_importer
  package

* ./dag/ directory contains one python file where the Airflow DAGs are defined.
  There are three DAGs defined in the file:
  * educational_data_import_dzi_csv - for importing DZI data
  * educational_data_import_nvo_csv - for importing NVO data
  * educational_data_delete_examination - deletes data for specified examination session

  The first two DAGs are quite similar, each of them:
  * first downloads a CSV specified via URL
  * uses the csv_importer.import_csv module to import the data.

* ./app.py - this is a CLI application which is an entry point to the
  ./csv_importer package, mainly to ./csv_importer/import_csv.py.
  Run `./app.py --help` for more information.

* ./postgres - the key thing here is the `docker-compose.yaml` file which
  brings up a postgres instance. It is quite useful for development needs.

  Additional the directory contains some sql files which probably should not
  be merged in the repo... but they are.

* ./bin - contains helper scripts, check their individual docs.

# Technical details

## Python virtual environment

In order to use or change the csv_importer package or the app.py
you need virtual environment. You can use any venv tool - venv, virtualenv,
pyenv, conda, etc.

With the venv tool of choice create virtual environment, activate it
and install in it the `requirements.txt`.

Steps to create venv with the python's venv module:

```
# Go to the repo root
cd <root of the repo>

mkdir -p csv_importer/venv
python3 -m venv csv_importer/venv
source csv_importer/venv/bin/activate
pip install -U pip
pip install -r ./csv_importer/requirements.txt
```


## Initializing Postgres DB

A new postgres database is initialized by

1. Executing the DB migrations with Alembic.
The command is `alembic upgrade head` and the target DB is defined
in the alembic's env.py. Check the Alembic section below for more details,
also Alembic documentation is nice source of information.

2. Currently the Subject table is filled by the `init-db` command of the
   app.py (this action should be implemented as alembic db migration).


## Working with Alembic

Alembic is a tool for managing DB migrations for applications using
SQLAlchemy.

### Initialization

Alembic was initialized like this

```
cd csv_importer/csv_importer/

# creates the alembic directory
alembic init alembic

```

Then csv_importer/alembic/env.py was changed to point to Models object from db_models.py

The alembic.ini was changed:
* to point local postgres db.
* to use naming for db migrations files which starts with timestamp

### Generating db migrations

NB: All these actions are applied on the DB specified in the `sqlalchemy.url`
in `csv_importer/alembic.ini` file.

The process of generating new DB migrations consists of these steps:
* Ensure your development DB is up to date with current set of DB migrations
  by calling this command:

```
cd csv_importer/csv_importer/
alembic upgrade head
```

* Change db_models.py (add/remove models, columns, indices, etc),
  then call this command to generate the new migration file:

```
cd csv_importer/csv_importer/
alembic revision --autogenerate -m '<migration description>'
```

Then to apply the new migrations on your DB run `alembic upgrade head` again.

## Importing into crunch.data-for-good.bg database from your machine

The `eddata` database on the Postgres server in crunch.data-for-good.bg machine
is accessible for writing with the user `eddata-writer`.
This user is allowed to establish connections only from the
crunch.data-for-good.bg machine.

In order to access the database for writing from your machine you can
open ssh tunnel to the postgres server like this:

```
# Note that the local port is 5435, in order to not overlap it with locally
# running postgres

ssh -L 5435:127.0.0.1:5432 root@crunch.data-for-good.bg
```

Then before executing the app.py export DB_URL variable like this:
```
export DB_URL="postgresql://eddata-writer:<password-goes-here>@localhost:5435/eddata"
```


# Misc

## To import a raw CSV file in postgres

One
1. can use the csv_max_lengths.py script to calculate the max lengths of
of all columns.
2. Create statement like this (tip: use LLM)
  ```sql
  CREATE TABLE schools_mon_test (
      school_id VARCHAR(20),
      name VARCHAR(150),
      institution_type VARCHAR(50),
      institution_type_detailed VARCHAR(60),
      funding_type VARCHAR(50),
      funded_by VARCHAR(60),
      activity_address VARCHAR(150),
      building_type VARCHAR(30),
      cadastre_code VARCHAR(50),
      latitude VARCHAR(15),
      longitude VARCHAR(15),
      region VARCHAR(20),
      municipality VARCHAR(20),
      place VARCHAR(40),
      address VARCHAR(150)
  );
  ```
3. Load the data

```
psql -d eddata

# call the create table statement
eddata=# create table .....

# load the data with \copy command from a CSV file
eddata=# \copy schools_mon_test from 'schools_mon.csv' with CSV HEADER;

# grant select permissions to all tables to eddata-reader,
# so that the new table(s) is also included
eddata=# GRANT SELECT ON ALL TABLES IN SCHEMA public to "eddata-reader";
```