# Migrations

Alembic migration artifacts for application tables belong here.

Revision files live under `versions/`.

## Local Development

The default development database is the project-root SQLite file
`uniquode.sqlite3`. It is ignored by Git.

Initialise or update the local schema with:

```sh
uv run migrate upgrade
```

Use direct Alembic commands only when you need Alembic-specific flags that the
project migration command does not expose.

Use explicit in-memory SQLite only for tests or deliberately ephemeral runs:

```text
sqlite+aiosqlite:///:memory:
```

## PostgreSQL

PostgreSQL database, user, role, and privilege provisioning happens outside
application startup. Staging and production environments must provide an
already-created database and login role with the required privileges before the
application or migrations connect.

The application owns table/index/constraint migrations through Alembic. It does
not create or destroy PostgreSQL databases, users, roles, or privileges during
ordinary startup.
