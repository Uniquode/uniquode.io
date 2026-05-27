## 1. Dependency And Configuration Boundary

- [x] 1.1 Add `envex` as a runtime dependency using `uv`.
- [x] 1.2 Add `dbscripts` from `https://github.com/deeprave/dbscripts` as a
  project dependency for explicit PostgreSQL lifecycle tooling.
- [x] 1.3 Introduce an envex-backed settings construction path for default
  application creation.
- [x] 1.4 Preserve explicit `Settings(...)` construction for tests and isolated
  app factories.
- [x] 1.5 Define supported environment variable names for application settings,
  including database URL configuration.

## 2. Database And Secret Handling

- [x] 2.1 Use envex `DATABASE_URL` support for database configuration.
- [x] 2.2 Preserve the accepted local SQLite development default when no
  database URL is supplied.
- [x] 2.3 Ensure PostgreSQL credentials are consumed from environment-provided
  configuration and are not committed or logged.
- [x] 2.4 Document that PostgreSQL database/user/role provisioning remains
  external to application startup.
- [x] 2.5 Ensure any `dbscripts` integration is only used by explicit operator
  commands or scripts, not by web application startup.

## 3. Dotenv Support

- [x] 3.1 Enable envex `.env` loading for local development configuration.
- [x] 3.2 Keep the configuration path compatible with envex encrypted/decrypted
  `.env` workflows.
- [x] 3.3 Ensure local `.env` files and local secret material remain ignored by
  version control.

## 4. Validation

- [x] 4.1 Extend `validate` to cover environment-backed configuration.
- [x] 4.2 Ensure `validate --verbose` masks database credentials and other
  secret-bearing values.
- [x] 4.3 Run `uv run validate --verbose`, `uv run ruff format --check`,
  `uv run ruff check`, `uv run ty check src/`, `gtimeout 30s uv run pytest`,
  and `uv run openspec validate add-environment-support --strict`.
