# 0001: Development and Implementation Platform

Date: 2026-05-19

Status: Accepted

## Context

This project is being initialized as a web server that supports an application. The core platform should make server-side application development direct, async-friendly, and compatible with ASGI deployment.

The project also needs a clear path for front-end rendering and persistence. Front-end work should be server-rendered by default unless a future decision introduces a richer client application. Persistence must be async-first and should avoid awkward sync bridges around database access.

The project also needs a consistent Python runtime, application manager, build backend, formatter, linter, language server, and type checker so project commands remain predictable from the start.

The project does not currently have a domain requirement that justifies NoSQL storage. MongoDB, ArangoDB, and DynamoDB do not share a practical standard abstraction for application-level portability. Attempting to support interchangeable NoSQL backends would force the persistence model down to a weak lowest-common-denominator API.

## Decision

Use FastAPI as the primary application framework, with Starlette as the underlying ASGI toolkit where lower-level primitives are useful.

Use Python 3.14 as the implementation runtime.

This is an **async-first Python project**. Async-first is a governing design constraint, not just a framework preference:

- Request handlers, service boundaries, persistence calls, and integration points should be designed for `async` operation.
- Prefer async-native libraries for network, database, file, queue, and integration work.
- Sync libraries or blocking calls require explicit justification and must be isolated behind adapters, background execution, or another boundary that prevents event-loop blocking.
- APIs introduced by this project should expose async interfaces where they may perform I/O now or in the future.
- Deployment must support ASGI handoff, including operation behind Gunicorn using an ASGI worker.

Use Jinja2 for server-rendered front-end templates. Jinja2's async rendering support should be enabled where templates call async functions or consume async data.

Use `uv` as the Python application manager and tool runner. Use `uv_build` as the build backend.

Use Ruff for formatting and lint checks:

- `uv run ruff format`
- `uv run ruff check`

Use `ty` as the Python language server and type checker. The baseline type-check command is `uv run ty check src/`.

Project commands that depend on project-installed Python packages or development tools must run through `uv run` so `$PATH` and `$VIRTUAL_ENV` are set by `uv`.

Use a relational SQL backend by default.

Use PostgreSQL as the production database.

Use SQLite for local development and lightweight tests where behavior remains portable. Tests that rely on PostgreSQL-specific behavior must run against PostgreSQL.

Use Tortoise ORM as the application ORM and database access layer. Use Tortoise's built-in migration system for schema changes.

Application code must not couple route handlers directly to database clients. Persistence access should sit behind application services or repository-style modules where that keeps domain behavior and database mechanics separate.

The persistence layer must remain async-first:

- Normal query, transaction, and migration workflows must not require routine sync-to-async bridges.
- Database operations must be awaited at application boundaries.
- Blocking database work must not run in request handlers.

The application should avoid promising backend portability across unrelated NoSQL engines. If a later capability needs document, graph, or key-value storage, that requirement should be captured in a new ADR.

If Tortoise fails an early validation spike, use SQLAlchemy 2 async with Alembic as the fallback.

The validation spike should cover:

- FastAPI lifespan integration.
- PostgreSQL connection configuration.
- SQLite connection configuration.
- Migration creation and application, including downgrade behavior.
- Transaction handling.
- Relationship modeling.
- Type-checker friction with `ty`.

## Consequences

FastAPI and Starlette make ASGI the default application model and keep the framework layer compatible with the project's async-first requirement.

Async-first design keeps I/O behavior explicit and prevents accidental event-loop blocking from becoming a hidden architectural constraint.

Server-rendered Jinja2 keeps the initial front-end simple and avoids committing to a separate JavaScript application before the product needs one.

Using Python 3.14 with `uv`, `uv_build`, Ruff, and `ty` keeps project management, builds, formatting, linting, editor feedback, and type checking aligned around a small Python-native toolchain. Running project tools through `uv run` keeps command behavior tied to project metadata and the managed environment.

Relational storage keeps the initial persistence model predictable and fits common web application requirements around relationships, constraints, transactions, and reporting.

PostgreSQL gives the production system a mature SQL database with strong integrity and operational tooling.

SQLite keeps local development and many tests lightweight, while the decision explicitly prevents treating SQLite as a perfect substitute for PostgreSQL-specific behavior.

Tortoise ORM keeps the application aligned with the async-first platform decision and offers a simpler Django-like model paradigm without taking on the full Django framework.

Choosing SQL now does not prevent later use of NoSQL for a specific capability, but that should be an explicit design decision rather than a generic portability goal.

## Follow-Up Decisions

- Define the initial application packaging and runtime command.
- Define the template, static asset, and form handling conventions.
