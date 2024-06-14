#!/usr/bin/env bash

set -eou pipefail

log() {
    echo "$@" >&2
}

SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/vars.sh"
REPO_DIR="$(realpath "${SCRIPT_DIR}/..")"

files_to_import=(
    "${REPO_DIR}/vocab/semantic-schools.ttl"
    "${REPO_DIR}/data/core/geography/queries/jurisdictions.ru"
    "${REPO_DIR}/data/core/geography/queries/places.ru"
    # "${REPO_DIR}/data/core/geography/queries/polygons_construct.ru" depends on ontorefine
    # ("${REPO_DIR}/data/core/geography/queries/osm_ids.rql" TODO: understand what's this
    # ("${REPO_DIR}/data/core/geography/queries/geosparql-enable.ru" TODO: understand what's this
    # ----
    # ("${REPO_DIR}/data/core/schools/construct.ru" depends on ontorefine
    "${REPO_DIR}/data/core/schools/from_wikidata.ru"
)

for file_to_import in "${files_to_import[@]}"; do
    if [[ "$file_to_import" == *.ttl ]]; then
        file_type="turtle"
    else
        file_type="sparql"
    fi
    "${SCRIPT_DIR}/import-file.sh" "$file_to_import" "$file_type"
done
