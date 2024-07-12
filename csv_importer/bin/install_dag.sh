#!/usr/bin/env bash

#
# This script installs the csv_importer DAGs on the Airflow machine.
# 1. It creates python virtual environment under directory specified via
#    AIRFLOW_VENV_DIR env var.
#    The venv cconsists of:
#      * requirements described in csv_importer/requirements.txt
#      * the csv_importer module installed in editable mode
#      * the apache-airflow python package with version specified via
#        AIRFLOW_VERSION env var
# 2. It copies the py file with the DAG definitions into directory specified
#    with AIRFLOW_DAG_DIR env var
#

set -euo pipefail

log() {
    echo $* >&2
}

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(cd "$SCRIPT_DIR/../.."; pwd)"
CSV_IMPORTER_DIR="$REPO_DIR/csv_importer"

log "SCRIPT_DIR: $SCRIPT_DIR"
log "REPO_DIR: $REPO_DIR"


check_var() {
    local var_name="$1"
    if [ ! -n "${!var_name+x}" ]; then
        log "Variable $var_name should be defined."
        exit 1
    fi
}

ensure_vnv() {
    local VENV_DIR
    VENV_DIR="$AIRFLOW_VENV_DIR/csv_importer"
    log "Creating $VENV_DIR directory"
    mkdir -p "$VENV_DIR"

    log "Create python venv in $VENV_DIR"
    python3 -m venv "$VENV_DIR"

    source "$VENV_DIR/bin/activate"

    log "Installing csv_importer in editable mode"
    pip install "apache-airflow==$AIRFLOW_VERSION"

    log "Installing $CSV_IMPORTER_DIR/requirements.txt"
    pip install -r "$CSV_IMPORTER_DIR/requirements.txt"

    (
        cd "$CSV_IMPORTER_DIR/"
        pip install -e .
    )
}


main() {
    check_var AIRFLOW_DAG_DIR
    check_var AIRFLOW_VENV_DIR
    check_var AIRFLOW_VERSION

    ensure_vnv

    cp "$CSV_IMPORTER_DIR/dag/dag_csv_importer.py" "$AIRFLOW_DAG_DIR"
}

main
