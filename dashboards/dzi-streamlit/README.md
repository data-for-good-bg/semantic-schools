This directory contains a Streamlit application for presenting
the educational data.

Initially it was started as dashboard for DZI data, but later we
decided that this app will present the NVO data as well.


# Directory organization

* `dashboard` directory contains the streamlit application code
* `docker-compose` directory contains docker-compose project file and
  also required configuration files
* In this directory there's also a Dockerfile and Makefile which facilitate
  building the docker image

* `db-exporter` directory contains outdated helper scripts for extracting
  csv file from postgres database


# Building the docker image

The docker image of the educational dashboard is named `data-for-good-bg/eddata`.

This can happen with the provided Makefile.

It supports building `production` and `staging` images.

At the moment of writing this document the difference between the
two images is the tag.
Also when building the production docker image the Makefile will
validate that the current branch is `main`.

Running the command below will produce the production image:
```bash
make build-prod
```

To build the staging image use:
```bash
make build-staging
```

# Deployment

For deploying the dashboard we use docker compose.

The `./docker-compose` directory contains almost everything
needed to deploy and run dashboard app.

Currently there's no automated way to deploy the app,
it is done manually by cloning the repo.

The steps roughly are:

```bash

cd /opt

# 1. clone the repo under the desired name, let say `production-eddata-dashboard`
git clone https://github.com/data-for-good-bg/semantic-schools.git production-eddata-dashboard

# 2. go to the docker-compose directory
cd production-eddata-dashboard/dashboards/dzi-streamlit/docker-compose

# 3. Create config/secrets.toml file, see below

# 4. Start the application
make up-production

# 5. Stopping the application is done similarly
make down-production
```

The `config/secrets.tom` file contains information for the
database connection. It should look like this:

```ini
[connections.eddata]
dialect = "postgresql"
host = "localhost"
port = "5432"
database = "<db-name>"
username = "<username>
password = "<password>"
```

The `./docker-compose/prod.env` and `./docker-compose/staging.env`
contain a list of environment variables which are used in the
docker-compose.yaml and allow changing the listening port,
the http path on which the streamlit app is running, etc.

The Makefile provides commands for starting and stopping
both production and staging instances of the application.
