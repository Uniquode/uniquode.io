## Why

[UT-239](https://linear.app/uniquode/issue/UT-239/add-site-startup-api)

Host applications currently carry Wevra boilerplate for framework, module, auth, database, settings, and route composition concerns. This makes each app responsible for details that should belong to the Wevra application engine and keeps recreating boundary leaks between app-owned behaviour and Wevra-owned infrastructure.

## What Changes

- Add a public Wevra startup API shaped around `site = wevra.start(app, config_source=...)`, where the host app may still own the `FastAPI()` instance.
- Introduce a `Site` object returned from startup to expose safe public settings, module, dependency, and helper access without exposing Wevra internals.
- Move common initialisation and setup concerns into Wevra, including module configuration, route registration, database wiring, module-owned settings construction, auth composition, and Wevra-specific runtime helpers.
- Keep host applications focused on their own product routes, pages, templates, and user-facing behaviour once `app.toml` or another config source is provided.
- Remove the need for host apps to manipulate Wevra-owned concerns such as auth settings, auth runtime state, FastAPI Users objects, database setup, route-prefix defaults, module route discovery, or environment-backed Wevra configuration.
- Preserve flexibility for host apps that need to construct `FastAPI()` directly so they can control app metadata, middleware, exception handlers, lifespan, docs URLs, instrumentation, and deployment-specific integration.
- Make Wevra-specific dependencies and helpers available through explicit public APIs, for example login-required dependencies, settings access, route/view definitions, and module capabilities.
- **BREAKING**: Existing host app composition code that manually initialises Wevra auth, database, module routes, or Wevra runtime state will be replaced by the central startup API.

## Capabilities

### New Capabilities

- `site-startup-api`: Public Wevra startup API and returned `Site` object for composing a configured FastAPI application from a config source.

### Modified Capabilities

- `application-infrastructure`: Host application composition requirements change so Wevra owns common engine setup while the app owns only product-specific behaviour.
- `configuration-service`: Configuration loading requirements change to support startup from an explicit config source passed by the host application or CLI.
- `module-settings-access`: Settings access requirements change so host apps obtain typed module settings and helpers through the `Site` API rather than reconstructing or inspecting Wevra internals.

## Impact

- Affected Wevra APIs: new `wevra.start(...)` or equivalent public startup entry point, new `Site` type, module composition hooks, settings access, route registration, auth composition, and database setup.
- Affected host app code: remove Wevra-specific FastAPI startup boilerplate and replace it with a single startup call plus explicit use of public Site/module helpers.
- Affected configuration: existing `app.toml` or other config sources remain the driver for modules, routes, database, auth, and module settings.
- Affected tests: Wevra gains coverage for startup composition and Site access; host app tests should cover only app-owned behaviour and integration with the public startup API.
- No new runtime dependency is expected unless a concrete startup requirement proves one is necessary.
