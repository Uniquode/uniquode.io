## Why

The project now needs a real identity foundation so administrative and later
user-facing workflows can rely on canonical local accounts, browser sessions,
and password-based local sign-in. Existing Python identity libraries can reduce
the amount of custom baseline authentication code, but the architecture must
remain extensible for TOTP, WebAuthn/passkeys, linked external identities, and
future API/OAuth2 work.

## What Changes

- **BREAKING** Replace the current Tortoise ORM persistence baseline with
  SQLAlchemy async and Alembic, while retaining PostgreSQL for production and
  SQLite for local/lightweight tests.
- Add FastAPI Users as the baseline local-account and authentication lifecycle
  dependency.
- Introduce canonical local user, account lifecycle, browser-session, password
  sign-in, password reset, and email verification conventions.
- Introduce `fastapi-users-auth-ext` as a standalone, application-independent
  module that extends FastAPI Users with advanced authentication capabilities.
- Define the addon as storage-portable through async protocols, with optional
  storage adapters rather than coupling it to the application database model.
- Capture TOTP, WebAuthn/passkey, recovery-code, and MFA challenge concepts as
  addon responsibilities, staged behind baseline local authentication.
- Define `auth-provider` as a future internal package boundary for OAuth2
  authorisation-server integration, expected to wrap Authlib rather than
  reimplement OAuth2 protocol machinery.
- Defer implementation of `auth-provider` until local users and the
  authorisation model provide stable users, groups, flags, and scopes.
- Add persistent development database behaviour so ordinary local development
  uses a project-root SQLite database while tests can still opt into in-memory
  SQLite.

## Capabilities

### New Capabilities

- `development-database`: Persistent project-root SQLite development database,
  explicit in-memory SQLite test support, and migration/startup conventions for
  local development versus PostgreSQL deployment environments. Linear:
  `UT-178`.
- `identity-authentication`: Local users, FastAPI Users integration, session
  authentication, password flows, bootstrap administration, and extension points
  for linked identities and later advanced authentication.
- `fastapi-users-auth-ext`: A standalone FastAPI Users addon for MFA and
  advanced authentication features including TOTP, WebAuthn/passkeys, recovery
  codes, and challenge-state protocols.
- `auth-provider`: An internal, framework-independent OAuth2 provider
  integration boundary built around Authlib and host-provided subject, client,
  token, consent, and scope services.

### Modified Capabilities

- `application-infrastructure`: Replace the accepted Tortoise ORM persistence
  baseline with SQLAlchemy async and Alembic for SQLite/PostgreSQL.

## Impact

- Runtime dependencies will add FastAPI Users and SQLAlchemy async migration
  tooling, and remove Tortoise ORM once the persistence boundary has moved.
- Default local development database configuration will move from in-memory
  SQLite to a Git-ignored project-root SQLite database file.
- In-memory SQLite remains supported for tests and explicitly configured
  ephemeral runs.
- Application infrastructure will move from Tortoise model/migration
  conventions to SQLAlchemy async model/session/Alembic conventions.
- Identity routes, services, templates, and tests will be added for the baseline
  local user lifecycle.
- A new package/module boundary will be introduced for
  `fastapi-users-auth-ext`, with no dependency on `uniquode` application code.
- A future internal `auth-provider` package boundary will be documented as an
  Authlib integration layer, independent of FastAPI Users and
  `fastapi-users-auth-ext`.
- Internal OAuth2 provider implementation remains out of scope for this change
  except for documenting the dependency relationship with users, groups, flags,
  and scopes.
