## 1. Persistence Baseline

- [x] 1.1 Update ADR 0001 and application infrastructure docs to replace Tortoise ORM with SQLAlchemy async and Alembic.
- [x] 1.2 Replace Tortoise runtime dependency with SQLAlchemy async and Alembic dependencies using `uv`.
- [x] 1.3 Replace Tortoise persistence configuration with async SQLAlchemy engine/session configuration for PostgreSQL and SQLite.
- [x] 1.4 Add Alembic migration structure and validation for migration discovery.
- [x] 1.5 Update tests and validation checks that currently assume Tortoise model or migration locations.
- [x] 1.6 Change the default development database URL to a Git-ignored project-root SQLite file while keeping in-memory SQLite explicit for tests.
- [x] 1.7 Add a clear Alembic-backed development database initialisation path for the local SQLite file.
- [x] 1.8 Document PostgreSQL staging/production provisioning expectations: database, user, roles, and privileges exist before application startup.

## 2. FastAPI Users Baseline

- [x] 2.1 Add FastAPI Users as a runtime dependency using `uv`.
- [x] 2.2 Define SQLAlchemy-backed local user and OAuth account models compatible with FastAPI Users.
- [x] 2.3 Configure the FastAPI Users database adapter, user manager, password hashing, and authentication backend.
- [x] 2.4 Implement browser login, logout, current-user, reset-password, and verification flows through application-owned HTML/API routes.
- [x] 2.5 Add email delivery hooks for reset-password and verification token flows without hard-coding a production mail provider.
- [x] 2.6 Implement initial administrative user bootstrap with tests for first-run and already-bootstrapped states.

## 3. Identity UX And Policy

- [x] 3.1 Add server-rendered login, logout, reset-password, verification, and account-status templates consistent with the HTML foundation.
- [x] 3.2 Define account creation policy for the first implementation, including whether registration is open, invitation-only, or admin-created.
- [x] 3.3 Add route and dependency helpers for resolving authenticated, optional, and anonymous browser users.
- [x] 3.4 Add a feature-flag/settings abstraction for optional identity integrations such as OAuth account linking, without coupling reusable modules to application settings.
- [x] 3.5 Ensure page, partial, and API error handling remains consistent for identity failures.

## 4. `fastapi-users-auth-ext`

- [x] 4.1 Create the independent `auth_ext` package/module boundary without imports from `uniquode`.
- [x] 4.2 Define async protocols for challenge storage, TOTP credential storage, WebAuthn credential storage, and recovery-code storage.
- [x] 4.3 Define addon router-extension conventions that avoid duplicate FastAPI route registration for replaced flows.
- [x] 4.4 Add a minimal MFA challenge-flow skeleton that can pause login after successful primary authentication and complete login through a FastAPI Users backend.
- [x] 4.5 Add package-level tests proving the addon core is storage-portable and application-independent.

## 5. Advanced Authentication Planning

- [x] 5.1 Add design notes or TODO markers for TOTP enrolment, confirmation, verification, disablement, and replay policy.
- [x] 5.2 Add design notes or TODO markers for WebAuthn relying-party configuration, registration, authentication, and credential management.
- [x] 5.3 Add design notes or TODO markers for recovery codes and account recovery policy.
- [x] 5.4 Record `auth-provider` as the future internal Authlib integration boundary for OAuth2 provider work.
- [x] 5.5 Record that internal OAuth2 provider implementation is deferred until local users and authorisation scopes/groups are defined.

## 6. Validation

- [x] 6.1 Add focused tests for SQLAlchemy persistence configuration and migration wiring.
- [x] 6.2 Add focused tests for FastAPI Users user lifecycle integration and browser-session authentication.
- [x] 6.3 Add focused tests for administrative bootstrap behaviour.
- [x] 6.4 Run `uv run ruff format --check`, `uv run ruff check`, `uv run ty check src/`, `gtimeout 30s uv run pytest`, and `openspec validate identity-foundation --strict`.
- [x] 6.5 Add verbose validation output that lists the concrete checks performed while preserving concise default output.
- [x] 6.6 Cover the persistent development database default, explicit in-memory override, and migration initialisation path through the `validate` command.
