# uniquode.io

[![Build Status](https://img.shields.io/github/actions/workflow/status/Uniquode/uniquode.io/tests.yml?branch=main&label=tests&logo=github)](https://github.com/Uniquode/uniquode.io/actions/workflows/tests.yml)
[![Security](https://img.shields.io/github/actions/workflow/status/Uniquode/uniquode.io/codeql.yml?branch=main&label=security&logo=github)](https://github.com/Uniquode/uniquode.io/security/code-scanning)
[![Maintenance](https://img.shields.io/badge/maintenance-active-brightgreen.svg)](https://github.com/Uniquode/uniquode.io)

`uniquode` is the FastAPI-based web application for `uniquode.io`.

The application is currently an early server-rendered FastAPI site with local
identity support.

## Current Foundations

- FastAPI/Starlette ASGI application with `uniquode_io.asgi:app` as the stable app
  import path.
- Jinja2 server-rendered pages with `htmx` used only for progressive
  enhancement.
- Package-owned static assets and templates under configured modules, including
  assets-owned runtime serving from `wybra.assets`, template rendering from
  `wybra.template`, web-facing security policy from `wybra.security`, reusable
  form and CSRF defaults from `wybra.forms`, error handling from
  `wybra.errors`, route composition from `wybra.core`, application-owned public page templates in
  `src/uniquode_io/templates/`, and identity defaults from `wybra.auth`.
- SQLAlchemy async persistence with Alembic migrations.
- Local account support using FastAPI Users, including password sign-in,
  database-backed browser sessions, password reset hooks, and email verification
  hooks.
- Account pages for sign in, sign out, account status, password reset, and email
  verification.

## Local Commands

Run the development server:

```sh
uv run wybra-runserver
uv run wybra-runserver --host 127.0.0.1 --port 8000
uv run wybra-runserver --reload
uv run wybra-runserver --no-reload
APP_RELOAD=1 uv run wybra-runserver
```

Additional Uvicorn arguments can be passed after `--`, for example to trust
forwarded headers from a local TLS-terminating proxy:

```sh
uv run wybra-runserver --host 127.0.0.1 --port 8000 -- --proxy-headers --forwarded-allow-ips 127.0.0.1
```

See [WEB-SECURITY.md](WEB-SECURITY.md) for reverse-proxy HTTPS setup and secure
session-cookie guidance.

## Configuration

Runtime configuration is loaded through `envex`, including local `.env` files.
`DATABASE_URL` is the database connection string. App settings use concise names
such as `APP_ENV`, `APP_NAME`, `CSRF_SECRET`, `CSRF_SECURE`, `RESET_SECRET`,
`VERIFICATION_SECRET`, `SESSION_COOKIE`, `SESSION_FORCE_SECURE`,
`SESSION_LIFETIME`, `PROVIDER_ENABLED`, `TOTP_MODE`, `PASSKEY_ENABLED`, and
`APP_RELOAD`.
`wybra.core` owns the reusable envex/app.toml settings-loading mechanics, while
`app.settings` owns this application's concrete settings fields, defaults,
deployment policy, CSRF policy, and identity policy adapter.

Application composition is loaded from `app.toml` in the project root,
or from the path named by `APP_CONFIG`. This file is the shared source for
configured modules and web resource defaults used by runtime startup, Alembic,
validation, and future project tooling. `wybra.db` discovers model metadata
from `<module>.models` and Alembic version locations from
`<module>/migrations/versions/` when those surfaces exist; it also owns the
reusable database URL parsing and async SQLAlchemy engine/session helpers. The
project `wybra-migrate` command loads the selected app config boundary and
passes those settings into the generic `wybra.db` migration command factory.
Page, partial, and API routes are discovered and registered through
`wybra.core` route composition from `<module>.routes` through a
`module_routers` export, and template context
providers are registered from `<module>.context` with `add_to_context`. Route
prefixes are configured per module router label so the application can mount,
for example, the `wybra.auth` account router at `/account`.
Validation targets are discovered from
`<module>.validation` through a `validation_targets` mapping. Runtime template
and static serving resolve configured module package sources directly, so an
earlier configured module can override a later module by providing the same
logical template or static path. `wybra.assets` owns `[app.assets]`, runtime
static serving, static URL resolution, asset validation, and static collection.
Static collection is only needed when exporting assets for an external static
server such as Nginx, and the reusable static export boundary writes the
composed logical static namespace to `[app.assets].root`.

```toml
[app]
database_url = "sqlite+aiosqlite:///app.sqlite3"
modules = [
  "app",
  "wybra.assets",
  "wybra.security",
  "wybra.forms",
  "wybra.api",
  "wybra.template",
  "wybra.errors",
  "wybra.auth",
]

[app.routes]
app = { default = "" }
wybra-security = {}
wybra-forms = {}
wybra-api = {}
wybra-template = {}
wybra-auth = { account = "/account", api = "" }

[app.runserver]
asgi_app = "uniquode_io.asgi:app"
reload_env = "APP_RELOAD"

[app.templates]
auto_reload = true
cache_size = 0

[app.assets]
url_path = "/static/"
root = "static"

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

The current identity browser surface is published by `wybra.auth.routes`;
default identity templates and safe identity template state are provided by
`wybra.auth`. Identity model metadata and migration revisions are bundled with
`wybra.auth` alongside those models. Template rendering and template context are
published by `wybra.template`; error handling is published by `wybra.errors`;
form and CSRF defaults are published by `wybra.forms`; static asset setup is
published by `wybra.assets`; security headers and CORS policy are published by `wybra.security`. Host
applications can override logical template and static paths from earlier
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

`uniquode.io` commits must use the `wybra` Git source in `pyproject.toml` so CI
can install dependencies without a sibling checkout. When working locally across
both repositories, switch to the sibling checkout source:

```sh
python ../wybra/scripts/wybra_source.py path
```

Before committing or pushing `uniquode.io`, switch back to the CI-safe Git
source:

```sh
python ../wybra/scripts/wybra_source.py git
python ../wybra/scripts/wybra_source.py check git -q
```

The `path` and `git` commands run `uv lock` and `uv sync`, so they may need
network access. The `check` command is used by the local pre-commit hook so the
local path source cannot be committed accidentally.

Run project validation:

```sh
uv run wybra-validate
uv run wybra-validate --verbose
uv run wybra-validate --verbose environment web persistence
```

Verbose validation lists the concrete checks performed for each target. Database
URLs printed by validation are redacted when credentials are embedded, for
example `postgresql+asyncpg://***:***@host.example/app`.

Project command wrappers such as `wybra-runserver`, `wybra-routes`, and
`wybra-validate` are published by the `wybra` package. The current application
remains the configured command target where appropriate, for example
`wybra-runserver` starts `uniquode_io.asgi:app` through `[app.runserver]` in the
selected app config file.

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
uv run wybra-migrate init
uv run wybra-migrate upgrade
```

Use `--database-url` to target an explicit database for one migration command:

```sh
uv run wybra-migrate --database-url sqlite+aiosqlite:///scratch.sqlite3 init
uv run wybra-migrate --database-url sqlite+aiosqlite:///scratch.sqlite3 upgrade
```

Use `--config` to select an explicit app config file for one host-tool
invocation:

```sh
uv run wybra-migrate --config config/app.toml current
uv run wybra-routes --config config/app.toml
uv run wybra-authmgr --config config/app.toml user list
```

PostgreSQL environments use `wybra-migrate init` for explicit database, user,
role, and privilege provisioning before `wybra-migrate upgrade` applies
application schema migrations.

Manage local identity users with the operator CLI:

```sh
uv run wybra-authmgr user create person@example.com
uv run wybra-authmgr user create admin@example.com --admin
uv run wybra-authmgr user create reader@example.com --group readers
uv run wybra-authmgr user update reader@example.com --add-group editors
uv run wybra-authmgr user update reader@example.com --rm-group readers
uv run wybra-authmgr user update reader@example.com --set-group operators
uv run wybra-authmgr user list
uv run wybra-authmgr user list --json
uv run wybra-authmgr user password person@example.com
uv run wybra-authmgr user delete person@example.com --force
```

Manage local authorisation scopes and groups with the same CLI:

```sh
uv run wybra-authmgr scope create document:read --description "Read documents"
uv run wybra-authmgr scope update document:read --description "Read published documents"
uv run wybra-authmgr scope list --json
uv run wybra-authmgr scope delete document:read

uv run wybra-authmgr group create readers --description "Readers" --scope document:read
uv run wybra-authmgr group readers update --scope document:write --rm-scope document:read
uv run wybra-authmgr group readers add-user person@example.com
uv run wybra-authmgr group readers add-group staff
uv run wybra-authmgr group readers show --json
uv run wybra-authmgr group effective-scopes person@example.com --json
uv run wybra-authmgr group readers remove-user person@example.com
uv run wybra-authmgr group readers remove-group staff
uv run wybra-authmgr group readers delete --force
```

`wybra-authmgr` timestamp arguments accept Unix seconds directly, such as
`--expires-at 4102444800`, or supported date/time strings parsed by
`dateparser`. Numeric input is interpreted first as Unix seconds, so use a
separated form such as `2025-01-01` for calendar dates.

`wybra-authmgr` is owned by the reusable authentication package and resolves
the same application config boundary as the other Wybra project tools: run it
from the app project, set `APP_CONFIG`, or pass `--config <path>`. It reads
`[auth]` from `app.toml`, with `DATABASE_URL` overriding `[app].database_url`
when explicitly set.

`wybra-authmgr` talks to the configured identity database directly. It is
not an API-backed remote administration client; that mode is deferred until
administrative API tokens and scopes exist. Passwords are entered through hidden
prompts by default, or read from stdin with `--password -` for operator
automation. Password changes revoke existing sessions unless `--no-revoke` is
supplied. Groups are the local authorisation mechanism: scopes are assigned to
groups, users are assigned to groups, and effective scopes are resolved through
direct and nested group membership. Scope deletion is refused while any group
uses that scope, and group deletion is refused while users, child groups, or
parent groups still reference that group. Password writes use the configured
`wybra.auth` password policy, which provides server-side validation and
strength feedback for future UI use.

The CLI distinguishes application admins from superusers. `--admin` marks an
account for elevated application administration, while `--superuser` is the
absolute FastAPI Users privilege flag. Superusers cannot be deleted or
deactivated, and the final superuser cannot be demoted. A user's preferred
timezone is stored only when explicitly supplied; otherwise presentation falls
back to the current server/application timezone at runtime.
