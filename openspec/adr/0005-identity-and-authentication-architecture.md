# 0005: Identity and Authentication Architecture

Date: 2026-05-20

Status: Provisional

## Context

The application needs a real user model rather than a single administrative login. Users must be able to sign in through local credentials and through federated identity providers.

The platform is browser-first and session-oriented for human users, but the project also expects API consumers and future OAuth2-based integrations.

The system must support:

- local user accounts that exist independently of any external identity provider;
- account creation through external login providers that creates a local account;
- linked external identities for a local user;
- local sign-in through passwords and future passkeys;
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

Use session-backed authentication as the primary browser login mechanism.

Support local password authentication for local accounts.

Use FastAPI Users for baseline local account lifecycle and authentication primitives where they fit the project identity model.

Keep application ownership of account creation policy, user-facing templates, email delivery, redirects, and project-specific error handling around FastAPI Users flows.

Plan for passkey support as a first-class local authentication method.

Plan for TOTP as an additional authentication factor for local accounts.

Introduce `fastapi-users-auth-plus` as a standalone addon boundary for advanced authentication features such as TOTP, WebAuthn/passkeys, recovery codes, and MFA challenge flows. Its Python import package should be `fastapi_users_auth_plus`.

Design `fastapi-users-auth-plus` to depend on FastAPI Users extension points and async storage protocols rather than on `uniquode` application modules, templates, settings, or database models.

Support API access through session-backed requests where appropriate and through API tokens for machine-oriented access.

Support OAuth2 client behaviour for external identity-provider integration.

Support local OAuth2 authorisation capability where project requirements call for it, while keeping the local account as the canonical user identity.

Design provider integration behind an extension boundary so additional providers such as Google, Apple, GitHub, and others can be added without changing the local account model.

Keep the internal OAuth2 provider separate from the advanced-authentication addon. Internal OAuth2 provider work belongs behind an internal `auth-provider` boundary and should be deferred until local users and the authorisation model provide stable subjects, groups, flags, and scopes.

## Consequences

The project gets one canonical user model even when multiple login methods are attached to the same person.

Account linking remains explicit, which reduces the risk of treating provider identities as the application's primary source of truth.

Session-first browser authentication fits the HTML-first UI architecture and keeps ordinary user login flows straightforward.

Using FastAPI Users reduces custom implementation for common identity lifecycle features, but it does not remove application responsibility for account policy, server-rendered UI, email delivery, and project-specific flow decisions.

Adding passkeys and TOTP raises the complexity of the credential model, recovery flows, and administrative support, but it avoids painting the project into a password-only corner.

Keeping advanced authentication in `fastapi-users-auth-plus` creates a reusable boundary and prevents TOTP/WebAuthn challenge flow code from becoming tightly coupled to this application. The trade-off is that the addon must maintain compatibility with FastAPI Users public extension points.

Supporting both OAuth2 client and local OAuth2 authorisation capability creates a broader identity surface area than a simple social-login implementation. That flexibility is intentional, but it should be implemented in staged slices rather than all at once.

Separating `auth-provider` from FastAPI Users and `fastapi-users-auth-plus` keeps delegated authorisation and token issuance distinct from user authentication and MFA. Authlib is expected to provide most OAuth2/OIDC protocol machinery for that later boundary.

API token support allows machine access without forcing browser-facing workflows onto non-browser consumers.

## Open Questions

- Whether API tokens belong only to users or may also belong to future system integrations or service accounts.
- Whether first-time provider login should always create an account or whether some providers should require invitation or administrative approval.
- What passkey and recovery flows are required before passkey support is considered production-ready.
- Which external provider should be implemented first.
- Whether TOTP or WebAuthn/passkeys should be the first concrete feature in `fastapi-users-auth-plus`.
- Which Authlib server primitives are sufficient for the later internal `auth-provider` integration.

## Follow-Up Work

- Define the user, credential, session, external identity, and API token models.
- Define local account bootstrap and administrative-user setup.
- Define password, passkey, TOTP, account-linking, and recovery workflows.
- Define the provider integration boundary and the first provider implementation slice.
- Define the `fastapi-users-auth-plus` addon boundary and its initial storage protocols.
- Define the internal `auth-provider` boundary after the authorisation model establishes groups, flags, and scopes.

## Revision Notes

- 2026-05-24: Added FastAPI Users as the baseline identity lifecycle dependency, introduced `fastapi-users-auth-plus` as the advanced-authentication addon boundary, and separated the future internal `auth-provider` OAuth2 provider boundary.
