# 0004: Identity and Authentication Architecture

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

## Decision

Use the local user account as the canonical identity record.

Represent external or social login providers as linked external identities associated with a local user account rather than as standalone user records.

Allow local accounts to exist without any linked external identity.

Allow a successful first-time login through an approved external provider to create a new local user account, subject to project-defined account creation policy.

Use session-backed authentication as the primary browser login mechanism.

Support local password authentication for local accounts.

Plan for passkey support as a first-class local authentication method.

Plan for TOTP as an additional authentication factor for local accounts.

Support API access through session-backed requests where appropriate and through API tokens for machine-oriented access.

Support OAuth2 client behaviour for external identity-provider integration.

Support local OAuth2 authorisation capability where project requirements call for it, while keeping the local account as the canonical user identity.

Design provider integration behind an extension boundary so additional providers such as Google, Apple, GitHub, and others can be added without changing the local account model.

## Consequences

The project gets one canonical user model even when multiple login methods are attached to the same person.

Account linking remains explicit, which reduces the risk of treating provider identities as the application's primary source of truth.

Session-first browser authentication fits the HTML-first UI architecture and keeps ordinary user login flows straightforward.

Adding passkeys and TOTP raises the complexity of the credential model, recovery flows, and administrative support, but it avoids painting the project into a password-only corner.

Supporting both OAuth2 client and local OAuth2 authorisation capability creates a broader identity surface area than a simple social-login implementation. That flexibility is intentional, but it should be implemented in staged slices rather than all at once.

API token support allows machine access without forcing browser-facing workflows onto non-browser consumers.

## Open Questions

- What subset of OAuth2 authorisation-server capability is required in the first implementation slice.
- Whether API tokens belong only to users or may also belong to future system integrations or service accounts.
- Whether first-time provider login should always create an account or whether some providers should require invitation or administrative approval.
- What passkey and recovery flows are required before passkey support is considered production-ready.
- Which external provider should be implemented first.

## Follow-Up Work

- Define the user, credential, session, external identity, and API token models.
- Define local account bootstrap and administrative-user setup.
- Define password, passkey, TOTP, account-linking, and recovery workflows.
- Define the provider integration boundary and the first provider implementation slice.
- Define the local OAuth2 authorisation-server scope if that capability is required early.
