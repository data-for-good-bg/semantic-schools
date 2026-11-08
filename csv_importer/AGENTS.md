# AGENTS.md

## Project domain

This is a python project for importing data for schools, aggregated data for
teachers, studends and results from Bulgarian NVO (Национално външно оценяване)
and DZI (Държавни зрелостни изпити) examination sessions.

The project can be started as command line application and or as an Airflow
DAG.

The database type is PostgreSQL.

The input sources could be different:
- downloaded files from data.egov.bg or URLs to the site
- queries made against wiki data
- other spread sheets obtained via the Bulgarian law for access to public
  information (ЗДОИ - Закон за достъп до обществена информация)

## Project Setup and Management

- Python is 3.10, because this is what is currently used on the crunch machine
  where we run the Airflow instance.
- Dependency management: `uv` and `pyproject.toml` are used
- Adding new dependency: use `uv add`
- Running the app can be done with: `uv run python3 -m app ...`
- Branching: Branch from `main` as `<author-name>/<feature>`
- Do not commit in `main` open pull requests

## DB schema and migrations

The database schema is defined with SQLAlchemy in `csv_importer/db_models.py`.
The db migrations are managed with alembic, the `csv_importer/alembic` directory
contains the migration versions and scripts.

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


## Constraints

- Ask before adding any external dependency.


## Ignore

Treat everything in `.gitignore` as off-limits to read or edit.
On top of that, never open:

- Secrets and `.env` files
- Large data files unrelated to the current task
- Vendored or generated code

## Behavioral guidelines

**Tradeoff:** These guidelines bias toward caution over speed.
For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

When handling exceptions:
- handle specific exception types
- do not swallow exceptions unless it is asked for

The tests:
* Every changed line should trace directly to the user's request.
* A new change should not bring any unused code


### 4. Python coding conventions

* Use single quotes for strings, double quotes for python docs
* Python functions should have type hints.
* When using type hints avoid using union types, use dedicated types like Optional
* Avoid using tuples with more than 2 elements for function arguments
  or return types, instead use dataclasses
