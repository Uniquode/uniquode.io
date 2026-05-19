# Architecture

ADR 0001 is the source of truth for the implementation platform.

Current baseline:

- Python 3.14
- FastAPI with Starlette where lower-level ASGI primitives help
- Async-first ASGI application design
- Jinja2 server-rendered templates when UI requirements need them
- `uv` and `uv_build`
- Ruff, `ty`, and pytest
- Relational SQL persistence
- PostgreSQL for production
- SQLite for local/lightweight tests where behavior remains portable
- Tortoise ORM with built-in migrations

Keep changes small and requirement-driven. Do not introduce runtime dependencies, framework structure, product UI, or domain models before an OpenSpec requirement needs them.

Application code must not couple route handlers directly to database clients. Persistence access should sit behind application services or repository-style modules where that keeps domain behavior and database mechanics separate.
