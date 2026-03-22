# Repository Guidelines

## Project Structure & Module Organization
`app/` contains the application code. Keep HTTP routes, templates, and static files in `app/interfaces/`; business orchestration and schemas in `app/application/`; core concepts in `app/domain/`; and database or external integration details in `app/infrastructure/`. `app/modules/` holds feature-oriented slices, while [`app/main.py`](E:\Projetos\Controle_de_pragas1.1\app\main.py) is the FastAPI entry point.

Tests live in `tests/` and follow the main feature areas (`test_auth.py`, `test_work_orders.py`, `test_nfe_*`). Documentation is in `docs/`. Packaging and local utility scripts are in `scripts/`. Generated artifacts belong in `build/`, `dist/`, `output/`, and `tmp/` and should not carry hand-edited source changes.

## Build, Test, and Development Commands
Use the project virtualenv when possible:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.venv\Scripts\python.exe -m pytest -q
docker compose up --build
powershell -ExecutionPolicy Bypass -File scripts\build_test_installer.ps1
```

The first command installs the app in editable mode with dev dependencies. `uvicorn` starts the local server. `pytest -q` runs the full test suite. `docker compose` boots the containerized stack. `build_test_installer.ps1` creates the Windows test launcher in `dist/`.

## Coding Style & Naming Conventions
Follow `.editorconfig`: 4 spaces for Python and Markdown, 2 spaces for YAML/JSON/HTML/CSS/JS, LF line endings, UTF-8. No formatter or linter is enforced in `pyproject.toml`, so keep style aligned with `docs/code-standards.md`.

Prefer clear domain names, small focused functions, and explicit side-effect names. Use `snake_case` for modules, functions, and test files; `PascalCase` for classes and Pydantic/SQLAlchemy models; and separate create/read/update schemas when contracts differ.

## Testing Guidelines
Pytest is configured via `pyproject.toml` with `tests/` as the test root. Name new files `test_<feature>.py` and add regression coverage for every bug fix. Cover both happy paths and blocking rules, especially authorization, stock movement, financial posting, PDF generation, and NFe integrations.

## Commit & Pull Request Guidelines
Recent history follows conventional prefixes such as `feat:`, `fix:`, `chore:`, and `docs:`. Keep commits scoped to one intent and write messages in the imperative, for example `fix: correct stock rollback on work order deletion`.

PRs should describe the functional change, affected layers, validation performed, and any config or migration impact. Link related issues when available, include screenshots for UI changes under `app/interfaces/web/`, and update docs/tests in the same change set.

## Security & Configuration Tips
Keep secrets only in `.env`; use `.env.example` and `.env.sefaz-homologacao.example` as templates. Do not commit real certificates, tokens, or production database snapshots. When touching fiscal or certificate flows, document assumptions in `docs/` and verify example-safe data only.
