# Commands

- `uv sync` — sync dependencies declared in `pyproject.toml` and locked in `uv.lock`.
- `uv run python manage.py test` — run the Django test suite from the repository root.
- `uv run python manage.py test backend.accounts` — run account tests only from the repository root.
- `docker compose up -d db` — start PostgreSQL for local `uv run` commands.
- `uv run python manage.py runserver 0.0.0.0:8000` — start Django at `http://localhost:8000/` after starting the database.
- `docker compose down` — stop the containers; the database volume is preserved.

Documents

- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`

# Rules

- Declare dependencies in `pyproject.toml`; ask before adding dependencies.
- Commit regularly
