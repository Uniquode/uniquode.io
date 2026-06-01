## Why

The project needs a real identity foundation, but that foundation should not be
owned by the `uniquode` application package. The existing top-level `auth_ext`
package is the starting point for that reusable component. It should own the
identity model, service API, FastAPI Users integration, persistence contracts,
and later advanced authentication behaviour for reuse by other FastAPI
applications.

`uniquode` should consume `auth_ext` as a host application. It should
provide web presentation, application settings adaptation, route composition,
and concrete deployment configuration without becoming a dependency of the
`auth_ext` package.

## What Changes

- Treat `identity-foundation` as a parent change with smaller sub-specs. The
  first sub-spec is `identity-refactor`, which is limited to structural package
  separation and test repair.
- Define `auth_ext` as the reusable package owner of identity models, APIs,
  options/config objects, persistence protocols, and FastAPI Users integration.
- Establish the dependency direction as `uniquode -> auth_ext ->
  fastapi-users`, with no imports from `auth_ext` back into `uniquode`.
- Add FastAPI Users as the baseline local-account and authentication lifecycle
  dependency of `auth_ext`.
- Define storage portability through `auth_ext` persistence protocols and
  concrete adapters, including SQLAlchemy async for the first implementation.
- Keep `uniquode` as the web interface and host integration layer for identity
  pages, templates, runtime settings adaptation, and route mounting.
- Capture canonical local user, account lifecycle, browser-session,
  password-sign-in, password-reset, email-verification, and bootstrap
  conventions as package capabilities exposed to host applications.
- Capture TOTP, WebAuthn/passkey, recovery-code, OAuth-account-linking, and
  MFA challenge concepts as `auth_ext` responsibilities, staged behind
  baseline local authentication.
- Define `auth_provider` as the future internal Authlib integration boundary
  for OAuth2/OIDC authorisation-server work, independent of `uniquode` and
  separable from baseline identity. Reserve `fastapi-oauth-provider` as the
  future distribution name if this boundary is extracted.
- Add persistent development database behaviour so ordinary local development
  uses a project-root SQLite database while tests can still opt into in-memory
  SQLite.

## Capabilities

### New Capabilities

- `identity-refactor`: Structural refactor that promotes the existing
  `uniquode.identity` shape into the independent top-level `auth_ext` package,
  keeps `uniquode` as the host/web interface, and repairs tests around the new
  dependency direction.
- `auth-ext-package`: Reusable FastAPI/FastAPI Users identity and
  authentication package, including `auth_ext` models, services, options,
  persistence contracts, adapters, and extension points.
- `identity-authentication`: Local users, FastAPI Users integration, session
  authentication, password flows, bootstrap administration, and extension points
  for linked identities and later advanced authentication.
- `development-database`: Persistent project-root SQLite development database,
  explicit in-memory SQLite test support, and migration/startup conventions for
  local development versus PostgreSQL deployment environments. Linear:
  `UT-178`.
- `auth-provider`: Future internal OAuth2/OIDC provider integration boundary
  implemented through the `auth_provider` Python package, built around Authlib
  and host-provided subject, client, token, consent, and scope services.

### Modified Capabilities

- `application-infrastructure`: Replace the accepted Tortoise ORM persistence
  baseline with SQLAlchemy async and Alembic for SQLite/PostgreSQL.

## Impact

- The first implementation slice is structural and should not add new user
  lifecycle behaviour beyond preserving the existing identity behaviour through
  the new package boundary.
- Runtime dependencies will add FastAPI Users and SQLAlchemy async migration
  tooling, and remove Tortoise ORM once the persistence boundary has moved.
- The reusable `auth_ext` package/module boundary will be expanded with no
  dependency on `uniquode` application code.
- `uniquode` will add only host integration code: settings adaptation, concrete
  persistence adapter selection, route mounting, and server-rendered
  presentation.
- Default local development database configuration will move from in-memory
  SQLite to a Git-ignored project-root SQLite database file.
- In-memory SQLite remains supported for tests and explicitly configured
  ephemeral runs.
- Internal OAuth2 provider implementation remains out of scope for this change
  except for documenting the dependency relationship with users, groups, flags,
  and scopes.
