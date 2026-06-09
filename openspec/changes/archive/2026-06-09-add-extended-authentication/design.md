## Context

The current identity foundation has a canonical local user model, password
login, browser-session issuance, and an authentication ceremony boundary. The
next layer is a shared external identity and account-linkage model that every
provider-specific implementation can consume.

## Goals / Non-Goals

**Goals:**

- Define reusable external provider identity records and local-user linkage.
- Define linking, unlinking, and callback resolution flows that keep the local
  user as the canonical identity.
- Define provider metadata and authentication method control in shared wevra storage
  so providers can be enabled consistently across projects.
- Keep provider enablement, runtime claims parsing, and account-creation policy
  out of this change.

**Non-Goals:**

- Do not implement concrete Google/GitHub/Apple runtime code here.
- Do not define TOTP, recovery-code, or passkey behaviour here.
- Do not define provider-account creation policy decisions beyond the shared flow
  contract.
- Do not define provider-specific policy enforcement beyond shared contract and
  conflict handling.

## Decisions

### Provider identity is canonical by local user

Provider identities should never replace the local account. A provider is always
resolved to a local account through a stable link record before ceremony or
session logic proceeds.

### Stable key is provider + provider subject

`provider_name` and `provider_subject` are the stable link key for lookup and
collision handling. Email is not an ownership proof on its own.

### Account-linkage contracts live in shared packages

`wevra.auth` and the FastAPI Users addon should own the protocol and service
contracts for provider identity records, callback assertions, and link lifecycle.

Storage and feature gating for these contracts are maintained by `wevra`; host
applications should consume shared contracts, with no additional schema changes
required for this change.

### Separate policy and provider rules from linkage contracts

Provider-specific policies (for example whether a provider assertion creates a
new local account) and provider-specific assertions stay in dedicated provider
and policy changes so that `UT-173` remains independently reviewable.

The "external_identity" wording here is the requirements namespace for this
change only; no new runtime abstraction layer is introduced beyond the existing
`wevra.auth`, `fastapi-users-auth-ext`, and `identity-authentication`
contracts.

### Persistence shape

Use a normalised shape:

- `identity_provider`: canonical provider identity rows keyed by provider name and
  provider subject, including provider-supplied metadata and feature configuration.
- `external_identity_link` (or equivalent): join table that maps local accounts to
  provider identities.

`provider_subject` is unique within a provider namespace rather than being unique
per user. `provider` plus `provider_subject` identifies an external identity
reliably.

Link ownership is one-to-one between local account and provider identity in the
link table to enforce a deterministic collision model.

## Migration Plan

1. Define `external-identity` plus `fastapi-users-auth-ext` and
   `identity-authentication` requirements for provider identity and linking.
2. Keep provider runtime changes in follow-on changes for Google, GitHub, and
   Apple.
3. Keep account-creation policy in `add-provider-based-account-creation-rules`.
