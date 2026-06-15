## 1. Audit And Ownership Classification

- [x] 1.1 Audit app configuration, environment, settings, validation, startup, route, view, and context files.
- [x] 1.2 Classify each remaining concern as app-owned, Wevra-owned, module-owned, or removable.
- [x] 1.3 Record any genuinely app-specific settings that must remain in the app.

## 2. Move Generic Environment And Config Support

- [x] 2.1 Move required environment loading/source behaviour from the app into Wevra-owned environment/config code.
- [x] 2.2 Move reusable config definition helpers and environment field mapping into Wevra or the owning module.
- [x] 2.3 Ensure Wevra commands no longer require an app-owned environment loader entry point.
- [x] 2.4 Encapsulate or simplify `envex` usage so host app code does not import or wrap it.

## 3. Rehome Module-Owned Settings

- [x] 3.1 Move database-related settings definitions and validation to the database module boundary.
- [x] 3.2 Move auth-related settings definitions and validation to the auth module boundary.
- [x] 3.3 Move web/static/template-related settings definitions and validation to the web module boundary.
- [x] 3.4 Replace cross-module app settings reads with config-service access, public helpers, or typed capabilities.

## 4. Clean The Host App

- [x] 4.1 Shrink app `Settings` to app-owned product settings only.
- [x] 4.2 Remove app-owned `environment.py` once Wevra command/startup call sites no longer use it.
- [x] 4.3 Remove app-owned `config_definitions.py` unless a product-specific config definition remains.
- [x] 4.4 Remove or rewrite app-level validation that duplicates Wevra/module validation.
- [x] 4.5 Remove package metadata hooks that point Wevra tooling at app-owned environment/config scaffolding.

## 5. Tests And Documentation

- [x] 5.1 Update Wevra/module tests for moved config, environment, and validation behaviour.
- [x] 5.2 Update app tests to assert app composition outcomes without duplicating Wevra internals.
- [x] 5.3 Add coverage proving startup works without database and auth modules when omitted.
- [x] 5.4 Add coverage proving compatible capability providers are not replaced by fallback Wevra modules.
- [x] 5.5 Update documentation and OpenSpec artifacts to describe the pristine app boundary.

## Notes Added During Implementation

- [x] N.1 Flatten app route surface from `app.routes` package to `app.routes` module.
- [x] N.2 Keep the generated/basic app health endpoint in `app.routes`.
- [x] N.3 Move home page handler to `app.views` and home page context to `app.context`.
- [x] N.4 Replace empty app validation package with simple `app.validation` module that demonstrates custom validation for the app-owned home page template and assets.
- [x] N.5 Move runtime static file ASGI app construction into `wevra.web.staticfiles`.
- [x] N.6 Add default-enabled Wevra template request context control so templates receive the current request unless explicitly disabled.
- [x] N.7 Move ASGI app loading boilerplate into `wevra.core.asgi.load_asgi_app`.
- [x] N.8 Keep app validation scoped to app-owned home route, health route, home template, and home static assets.
- [x] N.9 Move db/web/migration validation settings construction into Wevra-owned project settings.
- [x] N.10 Remove obsolete app `[tool.wevra]` settings-loader/configuration-error/database-url hooks.
- [x] N.11 Split app-owned config declarations into `app.config.module_config`; app settings must not import `APP_SETTINGS_CONFIG_DEF`.
- [x] N.12 Replace app `load_settings(environ, project_root, read_dotenv)` with Wevra-owned source resolution and settings-class-owned `ConfigDef`.
- [x] N.13 Rehome or remove `wevra.core.config.APP_SETTINGS_CONFIG_DEF`; `app_name` belongs to app config and `deployment_environment` belongs to Wevra runtime config.
- [x] N.14 Add a documented optional app `setup_site` stub so generated apps expose the startup extension point.
- [x] N.15 Replace raw template context dictionaries with immutable `TemplateContext` accumulation and update app context provider shape to accept `(request, context)` and return a new context.
- [x] N.16 Add `ConfigField(name=..., default=..., env=..., transform=...)` support so modules declare field-owned config resolution metadata in `ConfigDef` instead of parsing values in startup code.
- [x] N.17 Make `BaseSettings.load_settings()` infer single-section settings from `module_config` and align inputs through declared config fields.
- [x] N.18 Ignore and warn on template context provider overwrites while normalising deployment/web config validation failures at the Wevra boundary.
