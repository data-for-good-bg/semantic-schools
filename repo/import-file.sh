#!/usr/bin/env bash

set -eou pipefail

log() {
    echo "$@" >&2
}

SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/vars.sh"

IMPORT_FILE="${1:?-Specify file to import as first argument}"
FILE_TYPE="${2:?-Specify file type as second argument. Supported types are 'turtle' and 'sparql'.}"

if [ "$FILE_TYPE" != "turtle" ] && [ "$FILE_TYPE" != "sparql" ]; then
    log "Not supported file type $FILE_TYPE. Supported types are 'turtle' and 'sparql'"
    exit 1
fi



if [ "$FILE_TYPE" = "sparql" ]; then
    log "Importing sparql file $IMPORT_FILE"
    curl -X POST \
         -H "Accept:application/x-trig" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         --data-urlencode "update=$(cat "${IMPORT_FILE}")" \
         "${GRAPHDB_URL}/repositories/${REPO_ID}/statements"
else
    log "Importing turtle file $IMPORT_FILE"
    curl -X POST \
         -H "Content-Type:application/x-turtle" \
         -T "$IMPORT_FILE" \
         "${GRAPHDB_URL}/repositories/${REPO_ID}/statements"
fi

log "Imported $IMPORT_FILE"
