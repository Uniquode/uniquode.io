# 0005: Identity and Authentication Architecture

Date: 2026-05-20

Status: Provisional

## Context

The application needs a real user model rather than a single administrative
login. Users must be able to sign in through local credentials, passkeys, and
federated identity providers.

The platform is browser-first and session-oriented for human users, but the project also expects API consumers and future OAuth2-based integrations.

The system must support:

- local user accounts that exist independently of any external identity provider;
- account creation through external login providers that creates a local account;
- linked external identities for a local user;
- local sign-in through passwords and future passkeys;
- login ceremonies that can offer password, passkey, external-provider, TOTP,
  recovery-code, or later authenticator steps before final session issuance;
- additional authentication factors, including TOTP;
- browser sessions for user login;
- API access through sessions and/or API tokens;
- OAuth2 as a client capability for upstream identity providers;
- OAuth2 as a local authorisation capability where required by project use cases.

The architecture should stay extensible enough to support additional external providers without reshaping the core user model.

Identity-foundation planning selected FastAPI Users as the baseline library for standard local account lifecycle behaviour. FastAPI Users can cover common account, password, reset, verification, OAuth client login, authentication backend, and current-user primitives, while the application remains responsible for policy, UI, email delivery, and route-surface integration.

The same planning work identified TOTP, WebAuthn/passkeys, recovery codes, and multi-factor login challenges as advanced authentication concerns that should not be built directly into `uniquode` application code. They should live behind a standalone FastAPI Users addon boundary.

## Decision

Use the local user account as the canonical identity record.

Represent external or social login providers as linked external identities associated with a local user account rather than as standalone user records.

Allow local accounts to exist without any linked external identity.

Allow a successful first-time login through an approved external provider to create a new local user account, subject to project-defined account creation policy.

Use session-backed authentication as the primary browser login mechanism, backed
by database-stored FastAPI Users access tokens and delivered through HttpOnly
cookies.

Support local password authentication for local accounts.

Model browser login as an authentication ceremony rather than as a single
password-first flow. A password check, passkey challenge, external-provider
callback, TOTP code, recovery code, or other authenticator can be one step in
that ceremony. Final browser session state is issued only when the configured
policy requirements for the ceremony are satisfied.

Password success is therefore not always login completion. If policy requires
another authenticator, password success leaves the ceremony incomplete and the
login surface asks for the next required step. Passkeys and trusted external
providers may also be offered directly from the login surface and can complete
the ceremony without password or local MFA when policy allows.

Use FastAPI Users for baseline local account lifecycle and authentication primitives where they fit the project identity model.

Keep application ownership of account creation policy, user-facing templates, email delivery, redirects, and project-specific error handling around FastAPI Users flows.

Plan for passkey support as a first-class local authentication method.

Plan for TOTP as an additional authentication factor for local accounts.

Introduce `fastapi-users-auth-ext` as a standalone addon boundary for advanced authentication features such as TOTP, WebAuthn/passkeys, recovery codes, and MFA challenge flows. Its Python import package should be `auth_ext`.

Design `fastapi-users-auth-ext` to depend on FastAPI Users extension points and
async storage protocols rather than on `uniquode` application modules,
templates, settings, or `uniquode`-owned ORM models.

Treat the concrete local identity account model as part of the `auth_ext`
boundary. Because identity is the package's primary concern, `auth_ext` may add
or change reusable identity-account fields such as administration flags,
profile/display metadata, lifecycle timestamps, expiry state, and credential or
session-supporting relationships. Host applications such as `uniquode` consume
that model, pass options and integration hooks into it, and own presentation,
policy configuration, and application-specific authorisation built on top of
the identity data.

Treat local identity administration tooling as part of the `auth_ext` boundary
when it operates on the reusable `auth_ext` identity model. Package-owned tools
such as `usermgr` must use generic auth configuration, for example `auth.toml`
with `[auth]` sections, rather than importing host application settings or
depending on a host project root. A host application may share the same auth
configuration source, but it should not have to wrap or own the package CLI for
the CLI to be publishable with `fastapi-users-auth-ext`.

If `auth_ext` ships SQLAlchemy ORM models, they should live in an
`auth_ext.models` package that follows the platform `models` convention:
`models` is reserved for SQLAlchemy ORM models, and the package exposes
Alembic-ready `metadata` for host applications that explicitly enable those
models.

Support API access through session-backed requests where appropriate and through API tokens for machine-oriented access.

Support OAuth2 client behaviour for external identity-provider integration.

Allow configured external OAuth2 providers to participate in the authentication
ceremony. Provider success may complete the ceremony directly when the provider
is trusted for the requested policy, or may lead to additional local
authentication steps when policy requires them.

Support local OAuth2 authorisation capability where project requirements call for it, while keeping the local account as the canonical user identity.

Design provider integration behind an extension boundary so additional providers such as Google, Apple, GitHub, and others can be added without changing the local account model.

Keep the internal OAuth2 provider separate from the advanced-authentication addon. Internal OAuth2 provider work belongs behind an internal `auth-provider` boundary and should be deferred until local users and the authorisation model provide stable subjects, groups, flags, and scopes.

## Consequences

The project gets one canonical user model even when multiple login methods are attached to the same person.

Account linking remains explicit, which reduces the risk of treating provider identities as the application's primary source of truth.

Session-first browser authentication fits the HTML-first UI architecture and
keeps ordinary user login flows straightforward once an authentication ceremony
has completed. Using database-backed FastAPI Users session tokens keeps browser
authentication state revocable server-side rather than relying on a purely
stateless JWT cookie.

Using FastAPI Users reduces custom implementation for common identity lifecycle features, but it does not remove application responsibility for account policy, server-rendered UI, email delivery, and project-specific flow decisions.

Modelling login as a ceremony keeps passkeys, external providers, TOTP, and
recovery codes from becoming bolt-on post-login checks. It also allows a single
login surface to progressively offer or request the authenticators required by
policy.

Adding passkeys and TOTP raises the complexity of the credential model,
recovery flows, and administrative support, but it avoids painting the project
into a password-only corner.

Keeping advanced authentication in `fastapi-users-auth-ext` creates a reusable boundary and prevents TOTP/WebAuthn challenge flow code from becoming tightly coupled to this application. The trade-off is that the addon must maintain compatibility with FastAPI Users public extension points.

Publishing `auth_ext` ORM metadata through the standard model-package contract
keeps the addon reusable without giving it ownership of the host application's
Alembic migration tree or revision graph.

Allowing `auth_ext` to own and evolve the reusable local user model keeps
identity semantics out of the host application and makes the package viable as a
standalone FastAPI Users extension. The trade-off is that applications using
`auth_ext` accept its concrete identity schema as part of the package contract,
including migrations for fields that are common to identity administration but
not necessarily unique to one host.

Owning local identity administration tooling in `auth_ext` keeps operational
management aligned with the package schema and makes the CLI publishable with
the package. The trade-off is that `auth_ext` must provide generic
configuration and database-session bootstrapping for its tools rather than
relying on host-specific settings modules.

Supporting both OAuth2 client and local OAuth2 authorisation capability creates a broader identity surface area than a simple social-login implementation. That flexibility is intentional, but it should be implemented in staged slices rather than all at once.

Separating `auth-provider` from FastAPI Users and `fastapi-users-auth-ext` keeps delegated authorisation and token issuance distinct from user authentication and MFA. Authlib is expected to provide most OAuth2/OIDC protocol machinery for that later boundary.

API token support allows machine access without forcing browser-facing workflows onto non-browser consumers.

## Open Questions

- Whether API tokens belong only to users or may also belong to future system integrations or service accounts.
- Whether first-time provider login should always create an account or whether some providers should require invitation or administrative approval.
- Which external providers may satisfy local MFA policy by themselves and which
  should require additional local authenticators.
- What passkey and recovery flows are required before passkey support is considered production-ready.
- Which external provider should be implemented first.
- Whether TOTP or WebAuthn/passkeys should be the first concrete feature in `fastapi-users-auth-ext`.
- Which Authlib server primitives are sufficient for the later internal `auth-provider` integration.

## Follow-Up Work

- Define the user, credential, session, external identity, and API token models.
- Define local account bootstrap and administrative-user setup.
- Define authentication ceremony state and password, passkey, TOTP,
  account-linking, provider, and recovery workflows.
- Define the provider integration boundary and the first provider implementation slice.
- Define the `fastapi-users-auth-ext` addon boundary and its initial storage protocols.
- Define the internal `auth-provider` boundary after the authorisation model establishes groups, flags, and scopes.

## Revision Notes

- 2026-05-24: Added FastAPI Users as the baseline identity lifecycle dependency, introduced `fastapi-users-auth-ext` as the advanced-authentication addon boundary, and separated the future internal `auth-provider` OAuth2 provider boundary.
- 2026-05-28: Reframed browser login as an authentication ceremony that can
  include password, passkey, external-provider, TOTP, and recovery-code steps
  before final session issuance.
- 2026-05-29: Clarified that `auth_ext` must not depend on `uniquode`-owned ORM
  models and that any `auth_ext.models` package follows the SQLAlchemy metadata
  export convention.
- 2026-05-30: Clarified that the concrete reusable local identity account model
  belongs to `auth_ext`, so `auth_ext` may add or change identity-account fields
  while host applications consume the model and own presentation/policy
  integration.
- 2026-05-30: Clarified that local identity administration tools such as
  `usermgr` also belong to `auth_ext` when they operate on the reusable
  identity model, and should use generic `[auth]` configuration rather than
  host-specific settings.
