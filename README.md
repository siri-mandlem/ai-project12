# Library Desk

A Flask library catalog and loan tracker with account registration, book search,
checkout and return workflows, and a late-fine estimator.

## Run locally

Use Python 3.10 or later. From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
$env:SECRET_KEY = "replace-with-a-long-random-secret"
python -m backend.app
```

The local default is SQLite at `instance\library.db`. The application creates
its tables on startup. Set `DATABASE_URL` to a PostgreSQL connection string to
use PostgreSQL; both `postgres://` and `postgresql://` URLs are supported.
If a provider returns a `postgresql+psycopg://` URL, the app rewrites it to use
the installed Psycopg 2 driver automatically. Psycopg 3 is also installed to
support deployments that provide that driver-specific URL without rewriting.

## Deploy to Render

Create a Python web service from the project root with:

- Build command: `pip install -r backend/requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT backend.app:app`

Configure `DATABASE_URL` with a PostgreSQL connection string and set `SECRET_KEY`
to a unique random value in the service environment. The deployment workflow
can apply `database/schema.sql` to Neon before deploying. The app also performs
an idempotent `create_all` at startup for an empty database. Do not use the
development secret or SQLite for a multi-instance production deployment.

## Checks

```powershell
python -m unittest discover -s tests -v
python -m compileall -q backend tests
```
