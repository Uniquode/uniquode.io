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
- Tortoise-backed persistence with native Tortoise migrations.
- Local account support using Wybra auth, including password sign-in,
  Wybra request sessions, queued user-facing messages, password reset hooks,
  email verification hooks, passkeys, and external identity providers.
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
Database settings normally live in structured `[app.database]` configuration.
`DATABASE_URL` is an explicit database connection override. App settings use
concise names such as `APP_ENV`, `APP_NAME`, `CSRF_SECRET_KEY`, `CSRF_SECURE`,
`RESET_SECRET`, `VERIFICATION_SECRET`, `SESSION_COOKIE`,
`SESSION_FORCE_SECURE`, `SESSION_LIFETIME`, `PROVIDER_ENABLED`, `TOTP_MODE`,
`PASSKEY_ENABLED`, and `APP_RELOAD`.
`wybra.core` owns the reusable envex/app.toml settings-loading mechanics, while
`app.settings` owns this application's concrete settings fields, defaults,
deployment policy, CSRF policy, and identity policy adapter.

Application composition is loaded from `app.toml` in the project root,
or from the path named by `APP_CONFIG`. This file is the shared source for
configured modules and web resource defaults used by runtime startup,
validation, migrations, and project tooling. `wybra.db` discovers Tortoise
models from configured module model surfaces and owns the reusable database URL
parsing plus Tortoise connection lifecycle helpers. The project `wybra-migrate`
command loads the selected app config boundary and passes those settings into
Wybra's Tortoise migration integration.
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
modules = [
  "app",
  "wybra.secrets",
  "wybra.widgets",
  "wybra.messages",
  "wybra.assets",
  "wybra.security",
  "wybra.forms",
  "wybra.api",
  "wybra.template",
  "wybra.errors",
  "wybra.db",
  "wybra.auth",
  "wybra.providers",
  "wybra.media",
  "wybra.profile",
]

[app.database]
backend = "sqlite"
database = "app.sqlite3"

[app.routes]
app = { default = "" }
wybra-widgets = { partials = "", api = "" }
wybra-profile = { profile = "" }
wybra-security = {}
wybra-forms = {}
wybra-api = {}
wybra-template = {}
wybra-auth = { account = "/account", api = "" }
wybra-providers = { google = "/account/providers/google", github = "/account/providers/github", apple = "/account/providers/apple" }

[app.runserver]
asgi_app = "uniquode_io.asgi:app"
reload_env = "APP_RELOAD"

[app.templates]
auto_reload = true
cache_size = 0

[app.assets]
url_path = "/static/"
root = "static"

[wybra.sessions]
storage_backend = "database"
database_connection_name = "default"

[wybra.messages]
storage_backend = "session"

[wybra.forms]
csrf_token_secret_source = "keychain"
csrf_token_secret_key = "auth/forms/csrf-token-secret/dev/current"

[secrets.crypto]
source = "keychain"
current_key = "secrets/key/dev/current"
previous_keys = "secrets/key/dev/previous"

[secrets.keychain]
appname = "wybra"

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
identity management. The application database connection is `[app.database]`;
auth settings live in `[auth]` and `[auth.password.policy]`. `DATABASE_URL` is
the only database environment override for both runtime and auth tooling.

The current identity browser surface is published by `wybra.auth.routes`;
default identity templates and safe identity template state are provided by
`wybra.auth`. Identity model metadata and migration revisions are bundled with
`wybra.auth` alongside those models. Template rendering and template context are
published by `wybra.template`; error handling is published by `wybra.errors`;
form and CSRF defaults are published by `wybra.forms`; static asset setup is
published by `wybra.assets`; security headers and CORS policy are published by `wybra.security`. Host
applications can override logical template and static paths from earlier
configured modules.

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
network access. The local pre-commit hook performs a self-contained Git-source
check so the local path source cannot be committed accidentally.

Run project validation:

```sh
uv run wybra-validate
uv run wybra-validate --verbose
uv run wybra-validate --verbose environment web persistence
```

Verbose validation lists the concrete checks performed for each target. Database
URLs printed by validation are redacted when credentials are embedded, for
example `postgresql://***:***@host.example/app`.

Project command wrappers such as `wybra-runserver`, `wybra-routes`, and
`wybra-validate` are published by the `wybra` package. The current application
remains the configured command target where appropriate, for example
`wybra-runserver` starts `uniquode_io.asgi:app` through `[app.runserver]` in the
selected app config file.

From the workspace root, run the main checks:

```sh
uv run ruff format --check app/src app/tests
