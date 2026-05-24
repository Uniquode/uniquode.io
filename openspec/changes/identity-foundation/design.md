## Context

ADR 0005 establishes the local user account as the canonical identity record.
ADR 0006 expects later authorisation decisions to attach groups, flags, scopes,
and organisation assignments to that identity. The current application has no
real user model, no browser-session authentication, and no password lifecycle.

The project previously selected Tortoise ORM as the early persistence layer, but
the identity-library exploration changed that trade-off. FastAPI Users can
provide a mature baseline for local account lifecycle, authentication backends,
password reset, email verification token flows, OAuth client login, and current
user dependencies. Its currently supported database integrations are SQLAlchemy
and Beanie, while Tortoise would require an unsupported custom adapter.

Beanie/MongoDB would make FastAPI Users integration easier, but adopting a
document database primarily to satisfy the auth dependency would reverse the
accepted relational/PostgreSQL platform direction for a library-driven reason.
SQLAlchemy async keeps the project relational, aligns with PostgreSQL and
SQLite, and is already named in ADR 0001 as the fallback if Tortoise fails early
validation.

FastAPI Users does not solve every identity requirement. TOTP, WebAuthn/passkeys,
recovery codes, and local OAuth2 authorisation-server capability remain separate
work. The advanced-authentication extension should be designed as a standalone
addon around FastAPI Users rather than as application-specific code. The OAuth2
provider should be a separate internal `auth-provider` package boundary because
it is delegated authorisation and token issuance, not second-factor
authentication.

## Goals / Non-Goals

**Goals:**

- Move the storage baseline to SQLAlchemy async with Alembic for PostgreSQL and
  SQLite.
- Use a persistent project-root SQLite database as the default for ordinary
  local development while keeping in-memory SQLite available for tests.
- Add FastAPI Users for the baseline local user lifecycle.
- Establish local users, password sign-in, browser sessions, password reset,
  email verification hooks, and initial administrative bootstrap.
- Preserve a canonical local account model that can later link external
  identities.
- Gate optional identity integrations, such as OAuth account linking, through a
  settings abstraction rather than direct dependency on application settings.
- Introduce `fastapi-users-auth-ext` as a standalone addon boundary for
  advanced authentication.
- Define the addon around FastAPI Users extension points, async protocols, and
  optional storage adapters.
- Define `auth-provider` as a future internal Authlib integration boundary that
  remains independent of FastAPI Users and `fastapi-users-auth-ext`.
- Keep UI ownership in the application; libraries provide flows, APIs, and hooks
  rather than templates.

**Non-Goals:**

- Implement TOTP, WebAuthn/passkeys, or recovery codes in the first local-user
  slice unless explicitly selected as a follow-up task.
- Implement the internal OAuth2 authorisation provider before local users and
  authorisation policy exist.
- Publish the OAuth2 provider as a generic package unless future evidence shows
  Authlib does not cover the reusable protocol layer.
- Adopt MongoDB/Beanie for the whole application as part of this change.
- Couple reusable addon code to `uniquode` application modules, templates, or
  database models.
- Treat OAuth provider identities as the canonical user record.

## Decisions

### Use FastAPI Users for baseline local identity

FastAPI Users will provide the baseline account lifecycle and authentication
machinery where it fits: local users, password hashing integration, auth
backends, current-user dependencies, reset-password token flow, verification
token flow, and OAuth client login support.

Rationale: these are standard behaviours with significant security edge cases.
Using a focused library reduces bespoke code in the foundation slice while still
allowing the application to own policy, persistence configuration, and UI.

Alternative considered: build everything directly from Starlette/FastAPI,
`pwdlib`, `Authlib`, `PyOTP`, and `py_webauthn`. This maximises control but
front-loads common auth lifecycle work that FastAPI Users already handles.

### Move persistence to SQLAlchemy async and Alembic

The application persistence baseline will move from Tortoise ORM to SQLAlchemy
async plus Alembic, retaining PostgreSQL for production and SQLite for
local/lightweight tests.

Rationale: SQLAlchemy is an officially supported FastAPI Users backend, keeps the
relational database posture, avoids a custom Tortoise adapter, and preserves the
existing ADR fallback path. Alembic is the corresponding migration mechanism.

Alternatives considered:

- Tortoise adapter for FastAPI Users: keeps the previous ORM choice but makes the
  project own unsupported adapter behaviour for identity-critical code.
- Beanie/MongoDB: gives the easiest FastAPI Users integration and flexible
  document-shaped user records, but changes the platform database decision for a
  library integration reason rather than a domain requirement.

### Use persistent SQLite for local development by default

The default development database URL should point at a SQLite database file in
the project root, such as `sqlite+aiosqlite:///./uniquode.sqlite3`. That file
must be ignored by Git. In-memory SQLite remains supported through explicit
configuration for tests and one-off ephemeral runs.

Rationale: local identity work needs users, sessions, and reset/verification
state to survive application restarts. An in-memory default is useful for tests
but is a poor default for ongoing browser-based development and manual
verification.

Development SQLite schema creation must go through Alembic migration wiring or a
clearly named development setup path that applies migrations automatically or on
demand. The application must not silently create PostgreSQL databases, roles, or
privileges in staging or production. For PostgreSQL environments, the database
and user/role setup are expected to be provisioned before application startup;
the application only connects, and application operators apply migrations.

### Keep advanced authentication in a standalone addon

The distribution package should be named `fastapi-users-auth-ext`; the Python
import package should be `auth_ext`. It must not import
`uniquode` application code.

The addon will extend FastAPI Users at the route and flow boundary. It may
provide replacement routers for flows that need to pause login for a second
factor, but it must continue using FastAPI Users' user manager, auth backend, and
dependency model where those abstractions fit.

Rationale: TOTP and WebAuthn require stateful challenge flows around login. Those
flows should supplement FastAPI Users rather than fork it or register duplicate
routes that depend on route-order collisions.

### Gate optional integrations through a settings abstraction

Optional identity integrations must be explicitly enabled through a settings or
feature-flag abstraction before their routes or flows are exposed. OAuth
provider login, external account linking, and later advanced authentication
features should all have feature flags or equivalent configuration gates.

The `uniquode` application settings may contain the source configuration values,
but reusable modules such as `fastapi-users-auth-ext` must not import or depend
on the application's owned `Settings` type. The application should derive a
separate identity integration options object from `Settings` and pass that
object into reusable packages or application identity services.

Rationale: identity integrations often require provider credentials, callback
URLs, security policy, and user-facing support. Settings-backed flags allow the
application to keep dormant integrations present in code without accidentally
exposing incomplete or unconfigured behaviours.

Alternatives considered:

- Register routes only when implementation files are imported: too implicit and
  hard to audit.
- Rely only on missing provider credentials: fragile, because partial
  configuration mistakes become runtime behaviour rather than explicit policy.

### Use database-backed browser sessions

Baseline browser authentication will use FastAPI Users' database strategy with
an HttpOnly cookie transport. Session tokens are stored in the application
database and can be destroyed server-side on logout.

Rationale: this matches the HTML-first browser model better than a purely
stateless JWT cookie, keeps authenticated browser state revocable, and still
uses FastAPI Users' public authentication-backend abstraction.

### Protect server-rendered forms with shared CSRF checks

Server-rendered pages and partial routes must use a shared CSRF mechanism for
unsafe form submissions. The renderer supplies the configured field name and a
signed token, and the HTML dispatcher validates the token before state-changing
view code runs. Htmx or custom JavaScript requests that do not submit form data
can provide the same token through the configured CSRF header.

The CSRF nonce cookie is HttpOnly and SameSite=Strict. Local development may use
an insecure cookie for HTTP-only development servers, but non-local deployments
must use a secure CSRF cookie and a stable explicitly configured signing secret.

### Keep first account creation closed

The first implementation uses an `admin-created` account creation policy.
Public self-registration is not exposed. New local accounts are created through
controlled administrative/bootstrap paths until invitation or self-registration
requirements are accepted explicitly.

Rationale: closed account creation is the least risky default for an early
identity foundation. It avoids accidentally opening sign-up before authorisation,
abuse controls, email delivery, and operational support are complete.

### Use async protocols for addon storage

The addon core will define small async protocols for credential stores and
challenge stores. Storage adapters can then be provided separately for
SQLAlchemy, Beanie, Tortoise, Redis, or other backends.

Rationale: a standalone addon is only useful if it is not tied to this
application's persistence layer. Storage portability should be explicit at the
protocol boundary rather than inferred from ORM models.

### Defer the internal OAuth2 provider

The internal OAuth2 authorisation provider should not be implemented before
local users. It depends on stable subject identity, token persistence,
authorisation policy, groups, flags, and scope mapping. Those concepts belong
after the identity and authorisation foundations exist.

FastAPI Users can help with OAuth client login and authentication backends, but
it should not be treated as providing the project's full internal OAuth2
authorisation server. Authlib appears to cover the generic OAuth2/OIDC server
ground sufficiently that the project should not assume it needs to publish a
generic OAuth2 provider package. The later project package should therefore be
named `auth-provider` and treated as an internal integration layer around
Authlib.

`auth-provider` must remain independent of FastAPI Users and
`fastapi-users-auth-ext`. It should ask the host application for subjects,
clients, grants, tokens, consent, and scopes through explicit interfaces. In
`uniquode`, those interfaces can later be wired to FastAPI Users for current
browser users and to the authorisation foundation for group, flag, and scope
policy.

## Risks / Trade-offs

- [Risk] FastAPI Users is currently in maintenance mode. Mitigation: keep the
  integration narrow, pin compatible versions, avoid depending on private APIs,
  and cover our integration paths with focused tests.
- [Risk] Replacing Tortoise with SQLAlchemy changes an accepted platform
  decision. Mitigation: capture the change through OpenSpec and update ADR 0001
  when the change is accepted.
- [Risk] Automatically initialising databases can hide production provisioning
  mistakes. Mitigation: allow developer-friendly SQLite setup while documenting
  that PostgreSQL databases, roles, and privileges are pre-provisioned outside
  application startup.
- [Risk] FastAPI Users' default routers are API-shaped rather than designed for
  the project's HTML-first UX. Mitigation: build server-rendered page and
  partial routes in the application that call the identity services and library
  flows rather than adopting library UI assumptions.
- [Risk] Email behaviour may be overestimated. Mitigation: treat FastAPI Users
  as providing token routes and callbacks only; the application still owns mail
  delivery, templates, sender configuration, throttling, and operational policy.
- [Risk] Optional integrations can be accidentally exposed before they are
  configured or supported. Mitigation: require feature-flag abstractions for
  integration routes and account-linking flows without coupling reusable modules
  to the application `Settings` type.
- [Risk] Advanced authentication can become too coupled to this project.
  Mitigation: require `fastapi-users-auth-ext` to depend only on FastAPI,
  FastAPI Users, optional protocol libraries, and its own storage protocols.
- [Risk] MFA login can accidentally bypass second-factor policy through OAuth or
  another primary login path. Mitigation: centralise the post-primary-auth
  decision that chooses direct login versus challenge creation.

## Migration Plan

1. Update ADR 0001 and the main application infrastructure spec to replace
   Tortoise ORM with SQLAlchemy async and Alembic after this change is accepted.
2. Replace Tortoise runtime dependency and persistence modules with SQLAlchemy
   async engine/session configuration and Alembic migration conventions.
3. Change the default development database URL to a project-root SQLite file,
   keep in-memory SQLite as an explicit test configuration, and ensure the file
   is ignored by Git.
4. Add development migration initialisation or a clear setup path for applying
   Alembic migrations to the local SQLite database.
5. Document PostgreSQL deployment expectations: database/user/privileges exist
   before app startup and migrations are operator-controlled.
6. Add FastAPI Users and create the local user model, access-token model,
   database adapter wiring, database-backed cookie auth backend, and user
   manager.
7. Add application-owned HTML pages/partials and API routes for login,
   registration, password reset, verification, logout, and current-user status.
8. Add bootstrap logic for the initial administrative account.
9. Introduce `auth_ext` as an independent package/module with
   protocol-first storage interfaces and router-extension skeletons.
10. Document `auth-provider` as the future internal Authlib integration boundary.
11. Defer implementation of internal OAuth2 provider capability to a later change
   after the authorisation foundation defines groups, flags, and scopes.

## Open Questions

- Which email delivery provider or local development mail sink should be used?
- Which storage adapters should `fastapi-users-auth-ext` publish first:
  SQLAlchemy only, or SQLAlchemy plus Beanie?
- Should TOTP or WebAuthn be the first advanced-authentication feature built in
  the addon?
- How should account recovery work before both TOTP and WebAuthn are available?
- Which Authlib server primitives are sufficient for the later `auth-provider`
  implementation, and which small integration interfaces must the project own?
