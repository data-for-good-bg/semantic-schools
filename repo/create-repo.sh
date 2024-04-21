#!/usr/bin/env bash

set -eou pipefail

log() {
    echo "$@" >&2
}

SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/vars.sh"

REPO_CONFIG="${SCRIPT_DIR}/repo-config.ttl"
TMP_REPO_CONFIG=$(mktemp)
sed -s "s/__REPO_ID__/${REPO_ID}/g" "$REPO_CONFIG" > "$TMP_REPO_CONFIG"

REPO_URL="${GRAPHDB_URL}/rest/repositories/${REPO_ID}"

if curl -sf "${REPO_URL}" &>/dev/null; then
    log "Repo ${REPO_URL} exists, deleting it."
    curl -X DELETE "${REPO_URL}";
    log "Repo deleted."
fi


curl -X POST "${GRAPHDB_URL}/rest/repositories" \
    -H 'Content-Type: multipart/form-data' \
    -F "config=@$TMP_REPO_CONFIG"

log "Successfully created repo ${REPO_URL}".
