# uniquode.io

`uniquode` is the FastAPI-based web application for `uniquode.io`.

The application is currently an early server-rendered FastAPI site with local
identity support.

## Current Foundations

- FastAPI/Starlette ASGI application with `app.asgi:app` as the stable app
  import path.
- Jinja2 server-rendered pages with `htmx` used only for progressive
  enhancement.
- Package-owned static assets and templates under configured modules, including
  reusable web foundation defaults from `wevra.web`, application-owned public
  page templates in `src/app/templates/`, and identity defaults from
  `wevra.auth`.
- SQLAlchemy async persistence with Alembic migrations.
- Local account support using FastAPI Users, including password sign-in,
  database-backed browser sessions, password reset hooks, and email verification
  hooks.
- Account pages for sign in, sign out, account status, password reset, and email
  verification.

## Local Commands

Run the development server:

```sh
uv run wevra-runserver
uv run wevra-runserver --host 127.0.0.1 --port 8000
uv run wevra-runserver --reload
uv run wevra-runserver --no-reload
APP_RELOAD=1 uv run wevra-runserver
```

Additional Uvicorn arguments can be passed after `--`, for example to trust
forwarded headers from a local TLS-terminating proxy:

```sh
uv run wevra-runserver --host 127.0.0.1 --port 8000 -- --proxy-headers --forwarded-allow-ips 127.0.0.1
```

See [WEB-SECURITY.md](WEB-SECURITY.md) for reverse-proxy HTTPS setup and secure
session-cookie guidance.

## Configuration

Runtime configuration is loaded through `envex`, including local `.env` files.
`DATABASE_URL` is the database connection string. App settings use concise names
such as `APP_ENV`, `APP_NAME`, `CSRF_SECRET`, `CSRF_SECURE`, `RESET_SECRET`,
`VERIFICATION_SECRET`, `SESSION_COOKIE`, `SESSION_FORCE_SECURE`,
`SESSION_LIFETIME`, `OAUTH_LINKING`, `ADVANCED_AUTH`, and `APP_RELOAD`.
`wevra.core` owns the reusable envex/app.toml settings-loading mechanics, while
`app.settings` owns this application's concrete settings fields, defaults,
deployment policy, CSRF policy, and identity policy adapter.

Application composition is loaded from [app.toml](app.toml) in the project root,
or from the path named by `APP_CONFIG`. This file is the shared source for
configured modules and web resource defaults used by runtime startup, Alembic,
validation, and future project tooling. `wevra.db` discovers model metadata
from `<module>.models` and Alembic version locations from
`<module>/migrations/versions/` when those surfaces exist; it also owns the
reusable database URL parsing and async SQLAlchemy engine/session helpers. The
project `wevra-migrate` command is a `wevra.tools.migrate` adapter that loads
the configured host settings adapter from `[tool.wevra]` and passes those
settings into the generic `wevra.db` migration command factory.
Page, partial, and API routes are discovered and registered through `wevra.web`
from `<module>.routes` through a `module_routers` export, and template context
providers are registered from `<module>.context` with `add_to_context`. Route
prefixes are configured per module router label so the application can mount,
for example, the `wevra.auth` account router at `/account`.
Validation targets are discovered from
`<module>.validation` through a `validation_targets` mapping. Runtime template
and static serving resolve configured module package sources directly, so an
earlier configured module can override a later module by providing the same
logical template or static path. Static defaults from `wevra.web` are available
only when `wevra.web` is configured, unless an explicit filesystem `STATIC_ROOT`
is supplied. Static collection is only needed when exporting assets for an
external static server such as Nginx, and the reusable static export boundary
writes the composed logical static namespace to `[app.static].export_root`.

```toml
[app]
database_url = "sqlite+aiosqlite:///app.sqlite3"
modules = [
  "app",
  "wevra.web",
  "wevra.auth",
]

[app.routes]
app = { default = "" }
wevra-web = { partials = "", api = "" }
wevra-auth = { account = "/account", api = "" }

[app.templates]
auto_reload = true
cache_size = 0

[app.static]
url_path = "/static/"
export_root = "static"

[auth]
# Local development leaves session_cookie_force_secure unset so HTTP works.
# Non-local deployments must set SESSION_FORCE_SECURE=1 or configure
# session_cookie_force_secure = true in deployment-specific config.

[auth.password.policy]
minimum_length = 12
minimum_character_categories = 2
minimum_strength = 0.45
common_fragments = [
  "admin",
  "changeme",
  "changeit",
  "letmein",
  "p4ssw0rd",
  "pass",
  "password",
  "qwerty",
  "test",
  "tester",
  "welcome",
]
```

`app.toml` is not a secrets or deployment-policy file. Keep secrets in the
environment or deployment secret manager. It is the canonical normal
configuration boundary for the web runtime, migrations, validation, and local
identity management. The application database URL is `[app].database_url`;
auth settings live in `[auth]` and
`[auth.password.policy]`. `DATABASE_URL` is the only database environment
override for both runtime and auth tooling.

The current identity browser surface is published by `wevra.auth.routes`;
default identity templates and safe identity template state are provided by
`wevra.auth`. Identity model metadata and migration revisions are bundled with
`wevra.auth` alongside those models. Reusable layout, theme, error, form, and
stylesheet defaults are published by `wevra.web`; host applications can omit
`wevra.web` or override its logical template/static paths from earlier
configured modules.
Application-specific navigation and product policy remain application-owned.

Local `.env` files are for development only and are ignored by Git. Deployment
environments should inject secrets through their secret manager or environment
configuration.

Browser session cookies derive their `Secure` attribute from the request scheme:
plain HTTP responses use non-secure cookies, and HTTPS responses use secure
cookies. Local development leaves `session_cookie_force_secure` unset so HTTP
works without extra flags. Prefer trusted proxy-header normalisation for TLS
termination; set `SESSION_FORCE_SECURE=1` for non-local deployments and any
deployment where browser traffic is HTTPS but the ASGI request scheme cannot be
made reliable.
See [WEB-SECURITY.md](WEB-SECURITY.md) for Nginx and Apache examples. Non-local
deployments must explicitly configure identity token secrets and force secure
session cookies.

## Development Notes

Use `uv` for dependency and command execution. Runtime dependencies should be
added with `uv add`; development dependencies should be added with `uv add
--dev` or the appropriate dependency group option.

Run project validation:

```sh
uv run wevra-validate
uv run wevra-validate --verbose
uv run wevra-validate --verbose environment web persistence
```

Verbose validation lists the concrete checks performed for each target. Database
URLs printed by validation are redacted when credentials are embedded, for
example `postgresql+asyncpg://***:***@host.example/app`.

Project command wrappers such as `wevra-runserver`, `wevra-routes`, and
`wevra-validate` are published by the `wevra` package. The current application
remains the configured command target where appropriate, for example
`wevra-runserver` starts `app.asgi:app` through the `[tool.wevra]` adapter
metadata.

From the workspace root, run the main checks:

```sh
uv run ruff format --check app/src app/tests
uv run ruff check app/src app/tests
uv --directory app run ty check src/
uv --directory app run pytest -q
```

Initialise the local SQLite development database the first time, then apply the
schema migrations:

```sh
uv run wevra-migrate init
uv run wevra-migrate upgrade
```

Use `--database-url` to target an explicit database for one migration command:

```sh
uv run wevra-migrate --database-url sqlite+aiosqlite:///scratch.sqlite3 init
uv run wevra-migrate --database-url sqlite+aiosqlite:///scratch.sqlite3 upgrade
```

PostgreSQL environments use `wevra-migrate init` for explicit database, user,
role, and privilege provisioning before `wevra-migrate upgrade` applies
application schema migrations.

Manage local identity users with the operator CLI:

```sh
uv run wevra-authmgr user create person@example.com
uv run wevra-authmgr user create admin@example.com --admin
uv run wevra-authmgr user create reader@example.com --group readers
uv run wevra-authmgr user update reader@example.com --add-group editors
uv run wevra-authmgr user update reader@example.com --rm-group readers
uv run wevra-authmgr user update reader@example.com --set-group operators
uv run wevra-authmgr user list
uv run wevra-authmgr user list --json
uv run wevra-authmgr user password person@example.com
uv run wevra-authmgr user delete person@example.com --force
```

Manage local authorisation scopes and groups with the same CLI:

```sh
uv run wevra-authmgr scope create document:read --description "Read documents"
uv run wevra-authmgr scope update document:read --description "Read published documents"
uv run wevra-authmgr scope list --json
uv run wevra-authmgr scope delete document:read

uv run wevra-authmgr group create readers --description "Readers" --scope document:read
uv run wevra-authmgr group readers update --scope document:write --rm-scope document:read
uv run wevra-authmgr group readers add-user person@example.com
uv run wevra-authmgr group readers add-group staff
uv run wevra-authmgr group readers show --json
uv run wevra-authmgr group effective-scopes person@example.com --json
uv run wevra-authmgr group readers remove-user person@example.com
uv run wevra-authmgr group readers remove-group staff
uv run wevra-authmgr group readers delete --force
```

`wevra-authmgr` timestamp arguments accept Unix seconds directly, such as
`--expires-at 4102444800`, or supported date/time strings parsed by
`dateparser`. Numeric input is interpreted first as Unix seconds, so use a
separated form such as `2025-01-01` for calendar dates.

`wevra-authmgr` is owned by the reusable authentication package and resolves
the same application config boundary as the other Wevra project tools: run it
from the app project or set `APP_CONFIG`. It reads `[auth]` from `app.toml`,
with `DATABASE_URL` overriding `[app].database_url` when explicitly set.

`wevra-authmgr` talks to the configured identity database directly. It is
not an API-backed remote administration client; that mode is deferred until
administrative API tokens and scopes exist. Passwords are entered through hidden
prompts by default, or read from stdin with `--password -` for operator
automation. Password changes revoke existing sessions unless `--no-revoke` is
supplied. Groups are the local authorisation mechanism: scopes are assigned to
groups, users are assigned to groups, and effective scopes are resolved through
direct and nested group membership. Scope deletion is refused while any group
uses that scope, and group deletion is refused while users, child groups, or
parent groups still reference that group. Password writes use the configured
`wevra.auth` password policy, which provides server-side validation and
strength feedback for future UI use.

The CLI distinguishes application admins from superusers. `--admin` marks an
account for elevated application administration, while `--superuser` is the
absolute FastAPI Users privilege flag. Superusers cannot be deleted or
deactivated, and the final superuser cannot be demoted. A user's preferred
timezone is stored only when explicitly supplied; otherwise presentation falls
back to the current server/application timezone at runtime.
