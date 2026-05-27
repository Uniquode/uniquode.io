## Context

Runtime configuration now includes values that should not be committed to the
repository, most notably PostgreSQL credentials in the database URL. Local
development also needs a practical `.env` workflow while staging and production
should receive secrets from the deployment environment or a secret manager.

The current settings object is a plain dataclass. That is useful for tests and
explicit application factory construction, but it does not provide a standard
path for environment variables, `.env` files, encrypted `.env` workflows, or
typed database URL handling.

## Goals / Non-Goals

**Goals:**

- Use `envex` as the environment interface for application configuration.
- Support plain and encrypted/decrypted `.env` workflows through envex rather
  than custom parsing.
- Support `DATABASE_URL` through envex for SQLite and PostgreSQL configuration.
- Add `dbscripts` from `https://github.com/deeprave/dbscripts` for explicit
  PostgreSQL database lifecycle operations.
- Preserve constructor-based overrides for tests and explicit app construction.
- Keep local defaults safe and useful when no environment variables are set.
- Ensure validation can describe effective configuration without leaking
  secrets.

**Non-Goals:**

- Build a custom environment parsing framework.
- Store production secrets in the repository.
- Create PostgreSQL databases, users, roles, or privileges from application
  startup.
- Make destructive database lifecycle operations implicit.
- Replace deployment secret managers with `.env` files in staging or
  production.

## Decisions

### Use envex as the only environment abstraction

Application settings should read environment-backed values through `envex`.
The project should not introduce parallel custom helpers around `os.environ` or
manual `.env` parsing for application configuration.

Rationale: envex provides the type-safe environment interface requested for the
project, includes `.env` support, and already understands database URL style
configuration. Centralising on it keeps configuration behaviour consistent.

Environment variable names should stay concise. Conventional names such as
`DATABASE_URL` should be used as-is. App-specific names should use short,
readable names such as `APP_ENV`, `APP_NAME`, `APP_RELOAD`, `CSRF_SECRET`,
`CSRF_SECURE`, `RESET_SECRET`, `VERIFICATION_SECRET`, `SESSION_COOKIE`,
`SESSION_SECURE`, `SESSION_LIFETIME`, `OAUTH_LINKING`, and `ADVANCED_AUTH`
rather than a long project-name prefix.

### Keep explicit settings construction

`Settings(...)` should remain usable with explicit values. Environment loading
should be exposed through a clear factory or equivalent construction path used
by default app creation.

Rationale: tests, validation checks, and targeted app factories should not need
to mutate process environment just to exercise configuration variants.

### Treat database credentials as injected secrets

PostgreSQL credentials should enter the application through envex-backed
environment configuration, normally from the deployment platform's secret
manager. The application should consume the resulting database URL; it should
not create the PostgreSQL database or login role.

Rationale: database/user/role provisioning belongs to infrastructure. The
application owns schema migrations and runtime connections, not infrastructure
credential creation.

### Keep database lifecycle operations explicit

`dbscripts` should be available for explicit PostgreSQL database creation and
destruction workflows where that is useful for local, test, or operator-managed
environments. The web application must not call it during ordinary startup.

Rationale: creating and destroying databases is operationally useful but
destructive by nature. Keeping it behind explicit commands or provisioning
scripts avoids surprising production behaviour while still allowing this
self-authored utility to evolve with the project. If `dbscripts` later becomes an
async utility, the application can adopt that version without changing the
runtime configuration contract.

### Avoid leaking secrets in validation output

`validate --verbose` may report which configuration source or setting is active,
but it must not print full secret-bearing values such as PostgreSQL passwords.
Database URLs should be masked or reported by scheme/host/database only.

Rationale: validation output is diagnostic and likely to be copied into logs,
issues, or terminals. Secret-bearing configuration needs a stricter reporting
contract than ordinary paths and feature flags.

## Risks / Trade-offs

- [Risk] envex behaviour may not map exactly onto the current dataclass shape.
  Mitigation: introduce a narrow project settings factory and keep the dataclass
  as the application-facing value object if needed.
- [Risk] `.env` convenience can be mistaken for production secret management.
  Mitigation: document `.env` as local/development support and expect deployed
  environments to inject secrets externally.
- [Risk] validation output may accidentally expose credentials. Mitigation:
  centralise masking for secret-like values before printing effective settings.
- [Risk] database creation/destruction helpers could be used accidentally in
  runtime paths. Mitigation: keep `dbscripts` behind explicit operator commands
  or scripts and out of application startup.
