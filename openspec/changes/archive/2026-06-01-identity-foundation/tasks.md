## 1. `identity-refactor` Sub-Spec

- [x] 1.1 Add the `identity-refactor` sub-spec describing the structural package
  boundary.
- [x] 1.2 Promote the existing `uniquode.identity` implementation shape into the
  independent top-level `auth_ext` package.
- [x] 1.3 Ensure the top-level `auth_ext` package does not import `uniquode`,
  `uniquode.settings`, `uniquode.persistence`, templates, or application route
  modules.
- [x] 1.4 Keep `uniquode` as the host/web interface by adapting application
  settings into identity options and composing identity routes from the host.
- [x] 1.5 Preserve existing identity behaviour while changing structure; do not
  add new user lifecycle or authentication behaviour in this slice.
- [x] 1.6 Update imports, package metadata, and tests for the new dependency
  direction.
- [x] 1.7 Add an import-boundary test or equivalent validation that fails if the
  `auth_ext` package depends on `uniquode`.
- [x] 1.8 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.

## 2. Deferred Identity Foundation Sub-Specs

- [x] 2.1 Define the baseline local identity sub-spec after `identity-refactor`
  lands.
- [x] 2.2 Define the persistent development database sub-spec for `UT-178`
  separately from the structural refactor.
- [x] 2.3 Define advanced authentication sub-specs only after the reusable
  package boundary is stable.

## 3. Future Follow-Up Changes

- [x] 3.1 Create a future OpenSpec change for template-engine/module override
  support so independent modules such as `auth_ext` can provide base templates
  while applications can override them without moving template ownership into
  this slice.

## 4. `identity-authentication` Sub-Spec / `UT-207`

- [x] 4.1 Audit the current authentication implementation against the
  `identity-authentication` spec and record the baseline plan in
  `.todo/identity-authentication-plan.md`.
- [x] 4.2 Tighten the `identity-authentication` spec and design around the
  authentication ceremony model, optional public signup, and global
  inactive-account eligibility.
- [x] 4.3 Add minimal `auth_ext` ceremony result/finalisation APIs so password,
  future passkey, future MFA, and future provider paths can all complete login
  through the same session-issuance boundary.
- [x] 4.4 Route host password login through ceremony finalisation while
  preserving the current invalid-credential response, same-origin return target
  handling, and cookie-backed session behaviour.
- [x] 4.5 Centralise active-account eligibility checks before session issuance,
  current-user resolution, reset-password completion, verification completion,
  and future authenticator completion paths.
- [x] 4.6 Add account creation policy support for explicitly enabled public
  signup while keeping `admin-created` as the default.
- [x] 4.7 Add host-owned signup routing and templates only when public signup is
  enabled, using FastAPI Users account creation primitives through the
  `auth_ext` boundary.
- [x] 4.8 Keep TOTP, WebAuthn/passkeys, recovery codes, and external OAuth2
  providers as ceremony extension points only in this slice; do not implement
  their concrete authenticators yet.
- [x] 4.9 Add focused behaviour tests for ceremony finalisation, inactive-account
  exclusion, disabled/enabled signup policy, and preservation of existing
  browser-session, reset-password, and verification flows.
- [x] 4.10 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.

## 5. `auth-provider` Sub-Spec (`UT-208`)

- [x] 5.1 Align the `auth-provider` sub-spec name, design, and related identity
  wording with ADR 0007 terminology: `auth_provider` for the Python package
  boundary and `fastapi-oauth-provider` for the future distribution name.
- [x] 5.2 Add the first contract-only `auth_provider` package surface for
  host-owned provider options, subject/client/grant/token/consent/scope/signing
  key contracts, token lifetime options, and refresh-token storage policy.
- [x] 5.3 Keep runtime OAuth2/OIDC endpoint implementation deferred: do not add
  Authlib, token issuance, introspection, revocation, discovery, JWKS, consent,
  or grant endpoints in this slice.
- [x] 5.4 Add focused tests for provider option validation, refresh-token
  policy, host-neutral contract values, and the package import boundary.
- [x] 5.5 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.

## 6. `application-infrastructure` Sub-Spec (`UT-209`)

- [x] 6.1 Audit the current SQLAlchemy async, Alembic, validation, dependency,
  and CSRF infrastructure against the `application-infrastructure` sub-spec.
- [x] 6.2 Reserve `models` modules for SQLAlchemy ORM models and expose
  package-level `metadata` objects for migration consumption.
- [x] 6.3 Replace hard-coded Alembic metadata imports with a deterministic
  configured list of enabled model packages.
- [x] 6.4 Keep optional package metadata explicit so `auth_ext` and future
  `auth_provider` models are included only when their packages are enabled.
- [x] 6.5 Preserve route-handler decoupling from database clients and keep
  runtime dependencies requirement-scoped.
- [x] 6.6 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.

## 7. `development-database` Sub-Spec (`UT-178`)

- [x] 7.1 Confirm ordinary local development defaults to a persistent
  project-root SQLite database URL rather than in-memory SQLite.
- [x] 7.2 Preserve explicit in-memory SQLite support for tests and ephemeral
  runs.
- [x] 7.3 Keep the project-root SQLite database file excluded from version
  control.
- [x] 7.4 Add the `migrate` project command over Alembic for explicit schema
  initialisation and updates.
- [x] 7.5 Support `--database-url` migration overrides while keeping settings
  and envex resolution as the default.
- [x] 7.6 Prove the migration command can initialise an empty SQLite database
  with the current schema.
- [x] 7.7 Keep PostgreSQL database, user, role, and privilege provisioning
  outside application startup.
- [x] 7.8 Run `uv run ruff format --check`, `uv run ruff check`,
  `uv run ty check src/`, `gtimeout 30s uv run pytest`, and
  `uv run openspec validate identity-foundation --strict`.
