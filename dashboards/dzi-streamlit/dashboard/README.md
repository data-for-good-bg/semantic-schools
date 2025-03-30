A Streamlit app representing DZI data.

It works with CSV extract from the Postgres data. Check the `db-exporter`
directory for instructions how to create such CSV file.

# Creating the venv

This dashboard app uses [uv](https://docs.astral.sh/uv/) for managing requirements.

To create a new venv:

```
cd dashboards/dzi-streamlit/dashboard
uv venv
```

To install the requirements in it:
```
uv sync
```

If you prefer to use another venv tool, you can use also the generated with uv
requirements.txt file. Note that this file is manually exported and it might
be outdated from the dependencies described in pyproject.toml

# Start the dashboard

Before starting the dashboard you need to connect to a database.
You could run a DB locally or use the DB running on the crunch machine.
In either case you need to set the DB params in `dashboards/dzi-streamlit/dashboard/.streamlit/secrets.toml`
file.

```
cd dashboards/dzi-streamlit/dashboard
uv run streamlit run ./dashboard.py
```

# Running DB locally

There's docker-compose project in `csv_importer/postgres`.
You can go there and run it like this:

```
cd csv_importer/postgres
docker-compose up -d
```

To fill the database you need to run
 `./csv_importer/app.py import-dzi <file> --year <year>` to import at least
one DZI CSV file.

NB: This app runs with its own python venv.
