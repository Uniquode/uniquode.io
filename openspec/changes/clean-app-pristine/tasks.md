## 1. Audit And Ownership Classification

- [ ] 1.1 Audit app configuration, environment, settings, validation, startup, route, view, and context files.
- [ ] 1.2 Classify each remaining concern as app-owned, Wevra-owned, module-owned, or removable.
- [ ] 1.3 Record any genuinely app-specific settings that must remain in the app.

## 2. Move Generic Environment And Config Support

- [ ] 2.1 Move required environment loading/source behaviour from the app into Wevra-owned environment/config code.
- [ ] 2.2 Move reusable config definition helpers and environment field mapping into Wevra or the owning module.
- [ ] 2.3 Ensure Wevra commands no longer require an app-owned environment loader entry point.
- [ ] 2.4 Encapsulate or simplify `envex` usage so host app code does not import or wrap it.

## 3. Rehome Module-Owned Settings

- [ ] 3.1 Move database-related settings definitions and validation to the database module boundary.
- [ ] 3.2 Move auth-related settings definitions and validation to the auth module boundary.
- [ ] 3.3 Move web/static/template-related settings definitions and validation to the web module boundary.
- [ ] 3.4 Replace cross-module app settings reads with config-service access, public helpers, or typed capabilities.

## 4. Clean The Host App

- [ ] 4.1 Shrink app `Settings` to app-owned product settings only.
- [ ] 4.2 Remove app-owned `environment.py` once Wevra command/startup call sites no longer use it.
- [ ] 4.3 Remove app-owned `config_definitions.py` unless a product-specific config definition remains.
- [ ] 4.4 Remove or rewrite app-level validation that duplicates Wevra/module validation.
- [ ] 4.5 Remove package metadata hooks that point Wevra tooling at app-owned environment/config scaffolding.

## 5. Tests And Documentation

- [ ] 5.1 Update Wevra/module tests for moved config, environment, and validation behaviour.
- [ ] 5.2 Update app tests to assert app composition outcomes without duplicating Wevra internals.
- [ ] 5.3 Add coverage proving startup works without database and auth modules when omitted.
- [ ] 5.4 Add coverage proving compatible capability providers are not replaced by fallback Wevra modules.
- [ ] 5.5 Update documentation and OpenSpec artifacts to describe the pristine app boundary.
