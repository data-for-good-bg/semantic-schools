This directory contains scripts which facilitate GraphDB repository initialization.

The scripts are written in bash as PoC, but they will be re-written in Python
in order to automate the process with Airflow.

Script description:
* `create-repo.sh` is responsible to create a new repository described with
repo-config.ttl. The script also deletes the repository if such exists.
The deletion is a hacky way for avoiding duplication of triples.

* `init-repo.sh` is responsible to initialize repo data by importing turtle files
or executing sparql files.

* `import-file.sh` is a helper script which imports turtle or executes sparql file
in the repo.
