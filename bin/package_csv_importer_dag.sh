#!/usr/bin/env bash

log() {
    echo $* >&2
}

SCRIPT_DIR="$(dirname "$0")"
REPO_DIR="$(cd "$SCRIPT_DIR/.."; pwd)"

log "SCRIPT_DIR: $SCRIPT_DIR"
log "REPO_DIR: $REPO_DIR"

build_dir="$(mktemp -d)"

cleanup() {
    if [ "$build_dir" != "" ]; then
        log "Deleting build_dir $build_dir"
        rm -rf "$build_dir"
    fi
}


trap "cleanup" EXIT

cp_file() {
    log "copying $1 to $2"
    cp $1 $2
}


cp_file "$REPO_DIR/dags/dag_csv_importer.py" "$build_dir"
touch "$build_dir/__init__.py"

dst_csv_importer_dir="$build_dir/csv_importer"
mkdir -p "$dst_csv_importer_dir"

src_csv_importer_dir="$REPO_DIR/csv_importer"
src_files=("import_csv.py" "refine_csv.py" "models.py" "__init__.py")


for item in "${src_files[@]}"; do
    cp_file "$src_csv_importer_dir/$item" "$dst_csv_importer_dir"
done

mkdir -p "$REPO_DIR/build"
zip_name="$REPO_DIR/build/dag_csv_importer.zip"
if [ -e "$zip_name" ]; then
  rm "$zip_name"
fi

echo zip "$zip_name" "$build_dir/"
(
    cd "$build_dir"
    zip -r "$zip_name" ./
)
