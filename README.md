# Dreams Common Python

Shared Python utilities for Dreams applications. Install this package in your
projects to reuse logging, standard return codes, database services, and Flask
application setup without copying utility files between repositories.

The pip package name is `dreams-common`; the Python import name is `dreams_common`.
Requires **Python 3.11 or newer**. Installing from GitHub also requires Git.

## What's included

- **Logging:** `GetLogger`, `AddStdoutHandler`, and `AddFileHandler`.
- **Return codes:** the `RC` enum for consistent success and error results.
- **Database services:** PostgreSQL/Supabase and MySQL connection pools and query helpers.
- **Flask setup:** create an app, register blueprints, configure a CORS allowlist,
  and initialize repository classes with a shared database.

## Create a virtual environment

Run these commands in the application that will use this library (macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The following commands use the activated environment's Python and pip.

## Install from GitHub

```bash
python -m pip install "dreams-common @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

This installs the code on the repository's default branch. Keep the `git+https://`
prefix so pip clones the repository instead of downloading a GitHub HTML page.

The base install includes `boto3` and `supabase`, as declared in `pyproject.toml`.
Optional dependencies are installed only when you request the corresponding extra.

## Install optional dependencies

| Extra | Installs | Use it for |
| --- | --- | --- |
| `flask` | Flask and Flask-CORS | Flask app builder, blueprints, and CORS |
| `postgres` | Psycopg with binary driver and connection pool | Direct PostgreSQL connections, including Supabase-hosted PostgreSQL |
| `mysql` | MySQL Connector/Python | MySQL connections |

### Flask

```bash
python -m pip install "dreams-common[flask] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

### PostgreSQL / Supabase database

```bash
python -m pip install "dreams-common[postgres] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

The base `supabase` SDK dependency does not replace the `postgres` extra used by
the direct database service.

### MySQL

```bash
python -m pip install "dreams-common[mysql] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

### Combine extras

Separate extra names with commas, for example Flask plus PostgreSQL:

```bash
python -m pip install "dreams-common[flask,postgres] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

Or install all three:

```bash
python -m pip install "dreams-common[flask,postgres,mysql] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git"
```

Keep the quotes around install arguments, especially in zsh, so the shell does
not interpret the square brackets. Extras must exist in the GitHub revision you install.

## Install a specific version

Append a published Git tag to the repository URL. For example, **after `v1.0.1`
has been tagged and pushed**:

```bash
python -m pip install "dreams-common @ git+https://github.com/Eliaslopes248/dreams_common_libs.git@v1.0.1"
python -m pip install "dreams-common[flask,postgres] @ git+https://github.com/Eliaslopes248/dreams_common_libs.git@v1.0.1"
```

You can also replace the tag with a full commit SHA. Pinning a tag or commit keeps
applications on a known revision. Changing `version` in `pyproject.toml` alone
does not create a Git tag.

To upgrade to a newer release, use its tag with `--upgrade`:

```bash
python -m pip install --upgrade "dreams-common @ git+https://github.com/Eliaslopes248/dreams_common_libs.git@v1.0.1"
```

Replace `v1.0.1` with the release you want. Check the installed package metadata:

```bash
python -m pip show dreams-common
```

## Use the utilities

### Logging and return codes

```python
from dreams_common.logging.logger import GetLogger
from dreams_common.return_code.rc import RC

logger = GetLogger(__name__)
logger.info("Application started")


def do_work() -> RC:
    return RC.OK
```

### Flask application setup

Install the `flask` extra first. This example defines an app factory that accepts
your application's initialized database service:

```python
from flask import Blueprint, current_app

from dreams_common.flask_servers.repository import Repository
from dreams_common.flask_servers.server_builder import CreateFlaskApp
from dreams_common.return_code.rc import RC


class UsersRepository(Repository):
    # The inherited constructor stores the supplied database as self.db.
    pass


routes = Blueprint("users", __name__)


@routes.get("/health")
def health():
    repo = current_app.repos.users
    return {"database_configured": repo.db is not None}


def create_app(database):
    app, rc = CreateFlaskApp(
        database=database,
        repository_map={"users": UsersRepository},
        blueprint_list=[routes],
        cors_allowlist=["http://localhost:5173"],
        server_name=__name__,
    )
    if rc != RC.OK:
        raise RuntimeError("Unable to create Flask app")
    return app
```

Pass **repository classes**, not instances. The builder sets
`app.repos = RepositoryContainer(database, repository_map)`. Each class is
constructed with the shared database, and routes access it through
`current_app.repos.<name>`. An omitted or empty CORS allowlist allows no origins
through CORS. The example health route reports configuration only; it does not
check database connectivity.

## Develop this library locally

From the directory containing this project's `pyproject.toml`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Include extras when needed:

```bash
python -m pip install -e ".[flask,postgres,mysql]"
```

Editable installation makes local Python source edits available without reinstalling.
Re-run installation when you change dependencies or package metadata.

## Publish a version for GitHub installs

1. Update `version` in `pyproject.toml`.
2. Commit the release's code and metadata changes.
3. Create and push a matching tag.

For example, after committing version `1.0.2`:

```bash
git tag v1.0.2
git push origin HEAD
git push origin v1.0.2
```

Consumers can then install using `@v1.0.2`. Keep published tags unchanged and
create a new version for later releases. Publishing to PyPI is not required for
these GitHub installation commands.
