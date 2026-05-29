## Context

ADR 0005 establishes the local user account as the canonical identity record.
ADR 0006 expects later authorisation decisions to attach groups, flags, scopes,
and organisation assignments to that identity. The current application needs
local users, browser-session authentication, and password lifecycle support.

The identity foundation should not be shaped as an application-internal
`uniquode.identity` module. The intended architecture is the existing
top-level `auth_ext` package becoming the reusable FastAPI identity and
authentication component. It depends on FastAPI Users and exposes identity
models, service APIs, options, persistence contracts, and integration hooks.
`uniquode` is then a host application and web interface for those models and
APIs.

The dependency direction is:

```text
uniquode
  |
  v
auth_ext package
  -> fastapi-users
  -> persistence protocols/adapters
  -> identity options/config objects
```

There must be no reverse dependency from `auth_ext` into `uniquode`,
and no co-dependency between the two.

The project previously selected Tortoise ORM as the early persistence layer, but
the identity-library exploration changed that trade-off. FastAPI Users can
provide a mature baseline for local account lifecycle, authentication backends,
password reset, email verification token flows, OAuth client login, and current
user dependencies. Its currently supported database integrations are SQLAlchemy
and Beanie, while Tortoise would require an unsupported custom adapter.

Beanie/MongoDB would make FastAPI Users integration easier, but adopting a
document database primarily to satisfy the auth dependency would reverse the
accepted relational/PostgreSQL platform direction for a library-driven reason.
SQLAlchemy async keeps the first adapter relational, aligns with PostgreSQL and
SQLite, and is already named in ADR 0001 as the fallback if Tortoise fails early
validation.

FastAPI Users does not solve every identity requirement. TOTP,
WebAuthn/passkeys, recovery codes, linked external identities, and local OAuth2
authorisation-server capability remain separate work. `auth_ext` should own
extension points for these features, while `uniquode` owns the site-specific UI
and policy wiring.

## Goals / Non-Goals

**Goals:**

- Deliver identity foundation through smaller sub-specs, beginning with
  `identity-refactor` as a structural package-boundary change.
- Define `auth_ext` as a reusable FastAPI identity/authentication package, not
  as an application-owned `uniquode` module.
- Enforce one-way dependency from `uniquode` into `auth_ext`.
- Add FastAPI Users as the baseline local user lifecycle dependency of the
  `auth_ext` package.
- Establish package-owned local users, password sign-in, browser sessions,
  password reset, email verification hooks, and initial administrative
  bootstrap APIs.
- Preserve a canonical local account model that can later link external
  identities.
- Move the storage baseline to SQLAlchemy async with Alembic for PostgreSQL and
  SQLite, while keeping persistence access behind identity-owned contracts.
- Use a persistent project-root SQLite database as the default for ordinary
  local development while keeping in-memory SQLite available for tests.
- Gate optional identity integrations, such as OAuth account linking, through
  `auth_ext` options/config objects passed by host applications.
- Include extension points for advanced authentication: TOTP,
  WebAuthn/passkeys, recovery codes, and MFA challenge state.
- Define `auth_provider` as a future internal Authlib integration boundary that
  remains independent of FastAPI Users, `auth_ext`, and `uniquode`. Reserve
  `fastapi-oauth-provider` as the future distribution name if this boundary is
  later extracted.
- Keep UI ownership in host applications; `auth_ext` provides flows,
  APIs, routers, and hooks rather than product templates.

**Non-Goals:**

- Add new end-user identity behaviour in the `identity-refactor` sub-spec. That
  slice is limited to package structure and test repair.
- Implement TOTP, WebAuthn/passkeys, or recovery codes in the first local-user
  slice unless explicitly selected as a follow-up task.
- Implement the internal OAuth2 authorisation provider before local users and
  authorisation policy exist.
- Publish the OAuth2 provider as a generic package unless future evidence shows
  Authlib does not cover the reusable protocol layer.
- Adopt MongoDB/Beanie for the whole application as part of this change.
- Allow `auth_ext` to import `uniquode`, `uniquode.Settings`,
  `uniquode.persistence`, templates, or route modules.
- Treat OAuth provider identities as the canonical user record.
- Make `uniquode` the source of truth for identity-domain models.

## Decisions

### Start With `identity-refactor`

The first sub-spec is `identity-refactor`. It promotes the existing
`uniquode.identity` structure into the independent top-level `auth_ext`
package, updates imports and tests, and leaves `uniquode` as the host/web
interface.

This slice must preserve existing behaviour. It should not expand account
lifecycle, add new routes, change database semantics, or start the persistent
development database sub-issue. Those belong to later sub-specs.

Rationale: the dependency direction must be corrected before more identity
features are added. Once the package boundary is clean, later sub-specs can add
or refine authentication behaviour without carrying application-coupling debt.

### Make `auth_ext` Reusable And Host-Agnostic

Identity foundation code will live behind the reusable `auth_ext` package
boundary. The package owns the identity domain model, configuration objects,
persistence contracts, service APIs, and FastAPI/FastAPI Users integration.

`uniquode` consumes the package. It adapts its own application settings into
identity options, selects concrete persistence adapters, mounts routers, and
renders the site-specific HTML interface.

`auth_ext` is currently incubated inside this repository, but its API should be
shaped as if it may later be extracted as a standalone
`fastapi-users-auth-ext` distribution. The top-level package API should stay
focused on host-facing, storage-agnostic concepts.

Rationale: the identity model is valuable beyond this one site. Keeping
`auth_ext` host-agnostic prevents the current application from shaping APIs
that should be portable across FastAPI applications.

### Use FastAPI Users for Baseline Local Identity

FastAPI Users will provide the baseline account lifecycle and authentication
machinery where it fits: local users, password hashing integration, auth
backends, current-user dependencies, reset-password token flow, verification
token flow, and OAuth client login support.

Rationale: these are standard behaviours with significant security edge cases.
Using a focused library reduces bespoke code while still allowing `auth_ext` to
own policy, options, persistence contracts, and host-facing APIs.

Alternative considered: build everything directly from Starlette/FastAPI,
`pwdlib`, `Authlib`, `PyOTP`, and `py_webauthn`. This maximises control but
front-loads common auth lifecycle work that FastAPI Users already handles.

### Move Persistence to SQLAlchemy Async and Alembic

The first concrete persistence adapter will use SQLAlchemy async plus Alembic,
retaining PostgreSQL for production and SQLite for local/lightweight tests.

`auth_ext` must still expose persistence through package-owned contracts and
adapters rather than depending on `uniquode.persistence`. A SQLAlchemy adapter
can be shipped by `auth_ext`, while `uniquode` selects and configures it.

Within this project, `models` is reserved for SQLAlchemy ORM model modules.
Schemas, service contracts, options, and domain helpers should use names such as
`schemas`, `contracts`, `options`, or `services` rather than sharing the
`models` namespace. Each enabled model package should expose an exported
`metadata` object that Alembic can consume. The host application owns the
deterministic ordered list of enabled model packages, imports their `metadata`
objects, and owns the final Alembic migration tree and revision graph.

This gives reusable packages such as `auth_ext` and future `auth_provider`
clear migration candidates without relying on filesystem scans or importing
disabled optional components.

Alternatives considered:

- Tortoise adapter for FastAPI Users: keeps the previous ORM choice but makes
  the project own unsupported adapter behaviour for identity-critical code.
- Beanie/MongoDB: gives the easiest FastAPI Users integration and flexible
  document-shaped user records, but changes the platform database decision for
  a library integration reason rather than a domain requirement.

### Use Persistent SQLite for Local Development by Default

The default development database URL should point at a SQLite database file in
the project root, such as `sqlite+aiosqlite:///./uniquode.sqlite3`. That file
must be ignored by Git. In-memory SQLite remains supported through explicit
configuration for tests and one-off ephemeral runs.

Development SQLite schema creation must go through Alembic migration wiring or
a clearly named development setup path that applies migrations automatically or
on demand. The application must not silently create PostgreSQL databases, roles,
or privileges in staging or production. For PostgreSQL environments, the
database and user/role setup are expected to be provisioned before application
startup; the application only connects, and application operators apply
migrations.

### Keep Host UI Separate From Identity Package

`auth_ext` may expose service APIs, FastAPI dependencies, routers, and
response-neutral flow helpers. It must not impose product templates, site copy,
or a specific HTML layout.

`uniquode` owns server-rendered pages, partials, redirects, and presentation.
The host can call package services directly or mount package routers where that
is appropriate, but user-facing templates remain host-owned.

Package-owned templates are intentionally deferred. Future work should extend
the template engine so independent modules such as `auth_ext` can provide base
templates while the application can override them. That loader and override
model is outside this identity package slice.

### Gate Integrations Through Identity Options

Optional identity integrations must be explicitly enabled through `auth_ext`
options/config objects before their routes or flows are exposed. OAuth provider
login, external account linking, and later advanced authentication features
should all have feature flags or equivalent configuration gates.

The `uniquode` application settings may contain source configuration values, but
`uniquode` must adapt them into `auth_ext` options. `auth_ext` must not import
the application's `Settings` type.

### Use Database-Backed Browser Sessions

Baseline browser authentication will use FastAPI Users' database strategy with
an HttpOnly cookie transport. Session tokens are stored through the selected
identity persistence adapter and can be destroyed server-side on logout.

Rationale: this matches the HTML-first browser model better than a purely
stateless JWT cookie, keeps authenticated browser state revocable, and still
uses FastAPI Users' public authentication-backend abstraction.

### Model Login As An Authentication Ceremony

Login should be modelled as an authentication ceremony that can contain one or
more authentication steps before final browser session state is issued. A
password check, passkey challenge, TOTP code, recovery code, or future external
provider callback can all participate in that ceremony.

Password authentication success must not be treated as unconditional login
completion. If policy requires another factor, password success is an
intermediate ceremony outcome that keeps the user on the login surface and asks
for the next required authenticator. Likewise, passkey authentication should be
available directly from the login surface and may complete the ceremony without
password or MFA steps when policy allows.

This keeps MFA and passkeys from being tacked onto an already-completed login.
`auth_ext` extension points should therefore describe ceremony state,
available authenticators, required next steps, and final completion rather than
only exposing an "after password login" hook.

### Protect Server-Rendered Forms With Shared CSRF Checks

Server-rendered page and partial routes must use a shared CSRF mechanism for
unsafe form submissions. The host renderer supplies the configured field name
and signed token, and the host HTML dispatcher validates the token before
state-changing view code runs. Htmx or custom JavaScript requests that do not
submit form data can provide the same token through the configured CSRF header.

The CSRF nonce cookie is HttpOnly and SameSite=Strict. Local development may use
an insecure cookie for HTTP-only development servers, but non-local deployments
must use a secure CSRF cookie and a stable explicitly configured signing secret.

### Keep Public Signup Explicitly Gated

The default implementation uses an `admin-created` account creation policy.
Public self-registration is not exposed unless the host application explicitly
enables it through identity options. If public signup is enabled, the host owns
the signup route, templates, redirects, and post-create policy while `auth_ext`
provides the identity boundary around local account creation.

Newly created accounts must still follow the configured activation,
verification, and ceremony-completion policy. Signup should not imply immediate
browser authentication unless that is explicitly allowed by the account policy.

Initial administrative bootstrap must use a database-enforced singleton claim,
not only an application-level "does an admin exist?" check. This keeps the
first-admin path single-writer across multiple processes or tasks.

### Treat Inactive Accounts As Globally Ineligible

Inactive local accounts must be excluded at every authentication boundary. That
includes password sign-in, existing browser-session resolution, password reset
and verification token completion, future passkey and MFA challenge
completion, future external-provider callbacks, and final ceremony
finalisation.

The implementation should centralise this check as close as possible to
identity-session finalisation and token completion helpers. Individual routes
can still provide neutral responses, but they should not each carry their own
slightly different definition of account eligibility.

### Treat Advanced Authentication as Identity Package Scope

TOTP, WebAuthn/passkeys, recovery codes, and MFA challenge flows are `auth_ext`
responsibilities. They are not implemented in the baseline local-user slice,
but the baseline login ceremony must leave room for them as first-class
authenticators rather than bolt-on post-login checks. Their storage protocols,
ceremony state, challenge lifecycle, and completion rules should be designed
inside the reusable package boundary when those feature slices are selected.

Rationale: advanced authentication is part of the identity model, not a
`uniquode` site feature. Hosts should be able to reuse these `auth_ext`
capabilities with their own UI.

### Defer the Internal OAuth2 Provider

The internal OAuth2 authorisation provider should not be implemented before
local users. It depends on stable subject identity, token persistence,
authorisation policy, groups, flags, and scope mapping.

FastAPI Users can help with OAuth client login and authentication backends, but
it should not be treated as providing the project's full internal OAuth2
authorisation server. Authlib appears to cover the generic OAuth2/OIDC server
ground sufficiently that the project should not reimplement protocol machinery.
The provider boundary should therefore use `auth_provider` as its Python
package name and treat `fastapi-oauth-provider` only as a future distribution
name if extraction becomes useful.

`auth_provider` must remain independent of FastAPI Users, `auth_ext`, and
`uniquode`. It should ask the host application for subjects, clients, grants,
tokens, consent, scopes, and signing keys through explicit interfaces.

## Risks / Trade-offs

- [Risk] FastAPI Users is currently in maintenance mode. Mitigation: keep the
  integration narrow, pin compatible versions, avoid depending on private APIs,
  and cover integration paths with focused tests.
- [Risk] A reusable package boundary increases initial design work. Mitigation:
  define only the interfaces required by the first host integration, and let
  later hosts drive additional abstractions.
- [Risk] Replacing Tortoise with SQLAlchemy changes an accepted platform
  decision. Mitigation: capture the change through OpenSpec and update ADR 0001
  when the change is accepted.
- [Risk] Automatically initialising databases can hide production provisioning
  mistakes. Mitigation: allow developer-friendly SQLite setup while documenting
  that PostgreSQL databases, roles, and privileges are pre-provisioned outside
  application startup.
- [Risk] FastAPI Users' default routers are API-shaped rather than designed for
  the project's HTML-first UX. Mitigation: expose package services and
  presentation-neutral routers while keeping `uniquode` templates host-owned.
- [Risk] Email behaviour may be overestimated. Mitigation: treat FastAPI Users
  as providing token routes and callbacks only; host applications own mail
  delivery, templates, sender configuration, throttling, and operational policy.
- [Risk] Optional integrations can be accidentally exposed before they are
  configured or supported. Mitigation: require `auth_ext` feature options for
  integration routes and account-linking flows.
- [Risk] MFA login can accidentally bypass second-factor policy through a
  password, passkey, OAuth, or recovery path. Mitigation: centralise final
  authentication ceremony completion so no browser session is issued until the
  configured policy requirements have been satisfied.
- [Risk] Inactive-account checks can drift across password, session, token, and
  future provider/challenge paths. Mitigation: centralise active-account
  eligibility checks in identity helpers used before final session issuance and
  token-flow completion.

## Migration Plan

1. Update ADR 0001 and the main application infrastructure spec to replace
   Tortoise ORM with SQLAlchemy async and Alembic after this change is accepted.
2. Define the reusable `auth_ext` package boundary and move identity-domain
   models, options, services, persistence contracts, and FastAPI Users adapters
   there.
3. Replace Tortoise runtime dependency and persistence modules with SQLAlchemy
   async engine/session configuration and Alembic migration conventions.
4. Change the default development database URL to a project-root SQLite file,
   keep in-memory SQLite as an explicit test configuration, and ensure the file
   is ignored by Git.
5. Add development migration initialisation or a clear setup path for applying
   Alembic migrations to the local SQLite database.
6. Document PostgreSQL deployment expectations: database/user/privileges exist
   before app startup and migrations are operator-controlled.
7. Add FastAPI Users integration in `auth_ext`: local user model,
   access-token model, database adapter wiring, database-backed cookie auth
   backend, and user manager.
8. Add package services and host-facing APIs for the baseline authentication
   ceremony, logout, current-user, password reset, email verification, and
   initial administrative bootstrap.
9. Add `uniquode` host integration that adapts settings, selects persistence,
   mounts routes, and renders server-owned identity pages.
10. Add explicitly gated public signup only when account policy enables it.
11. Keep advanced-authentication extension skeletons inside the reusable
    `auth_ext` package boundary.
