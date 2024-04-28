# Intro

This directory contains python code which will handle importing NVO and DZI
data provided by egov.data.bg into relational or graph DB.

The initial version is quite simple:

1. Python code will be used to convert the various CSV files into the same
format.


2. Python code will push the refined CSV files into relational DB (sqlite, Postgres, BigQuery)
sqlachemy library will be used in order to support different SQL engines.

The long term version probably will be something like this:

1. Python code will be used to convert the various CSV files into the same
format.

2. Python code and SPARQL will be used to import scores data into GraphDB from
the refined CSV files

3. Python code and SPARQL will be used to import information for city, villages,
schools, into GraphDB

4. Python code will be used to create relational database from the GraphDB.


# Technical

## Working with sqlite

sqlite is used for dev-test cycle.

In order to create empty sqlite file execute:
```
sqlite3 /path/to/file.sqlite "VACUUM;"
```

## Working with alembic

### Initialization

alembic was initialized like this

```
cd csv_importer/

# creates the alembic directory
alembic init alembic

```

Then alembic/env.py was changed to point to Models object from models.py

The alembic.ini was changed:
* to point local sqlite db.
* to use naming for db migrations files which starts with timestamp

### Generating db migrations

NB: All these actions are applied on the DB specified in the `sqlalchemy.url`
in `csv_importer/alembic.ini` file.

Before changing models.py you need to have a DB which is up-to-date with current migrations. Call this:

```
alembic upgrade head
```

After you're ready with models.py updates call this to generate the new
migrations file.

```
alembic revision --autogenerate -m '<migration description>'
```

Then to apply the new migrations on your DB run `alembic upgrade head` again.
