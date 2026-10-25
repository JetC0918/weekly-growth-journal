# Commands

- `uv sync` — sync dependencies declared in `pyproject.toml` and locked in `uv.lock`.
- `uv run python manage.py test` — run the Django test suite.
- `uv run python manage.py test accounts` — run account tests only.
- `docker compose up -d db` — start PostgreSQL for local `uv run` commands.
- `docker compose up --build` — start Django and PostgreSQL at `http://localhost:8000/`.
- `docker compose down` — stop the containers; the database volume is preserved.

Documents

- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`

# Rules

- Declare dependencies in `pyproject.toml`; ask before adding dependencies.
- Commit regularly