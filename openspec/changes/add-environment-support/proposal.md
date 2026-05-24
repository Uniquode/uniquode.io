## Why

The application now needs deployment-safe configuration for values such as
database credentials, session policy, and local development defaults. The
current `Settings` dataclass only accepts constructor values, which leaves
runtime secrets and `.env`-backed local configuration outside the application
configuration contract.

## What Changes

- Add environment-backed application configuration using the `envex` module.
- Use envex's type-safe environment access and `.env` support, including its
  encrypted/decrypted `.env` capabilities where appropriate.
- Use envex `DATABASE_URL` support for database configuration, including
  PostgreSQL credentials supplied by deployment environments.
- Add `dbscripts` from `https://github.com/deeprave/dbscripts` as a project
  dependency for
  explicit PostgreSQL database lifecycle tooling.
- Preserve safe local defaults for development, including the project-root
  SQLite default selected by the identity foundation work.
- Keep explicit constructor/test overrides available so tests and isolated
  application factories do not require process environment mutation.
- Extend `validate` so configuration checks can report the effective
  environment-derived settings without exposing secret values.

## Capabilities

### New Capabilities

- `environment-configuration`: Type-safe environment and `.env` backed settings,
  based on envex, for application runtime configuration and secret injection.
  Linear: `UT-180`.

### Modified Capabilities

- `application-infrastructure`: Settings construction becomes environment-aware
  while keeping the application factory importable and test-configurable.

## Impact

- Dependencies will add `envex` and `dbscripts` through `uv`.
- Application settings construction will gain environment and `.env` loading.
- Database configuration will support deployment-provided `DATABASE_URL`
  values without committing credentials.
- PostgreSQL database creation/destruction may be supported by explicit
  operator tooling backed by `dbscripts`; it remains outside web application
  startup.
- Local commands and validation output may show effective non-secret
  configuration values for diagnostics.
- Existing direct `Settings(...)` usage in tests should continue to work.
