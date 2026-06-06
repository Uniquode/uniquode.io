## Context

The current identity foundation has a canonical local user model, password
login, browser session issuance, inactive-account exclusion, password reset and
verification flows, and a small authentication ceremony boundary. ADR 0005
already states that password success is not necessarily final login completion:
TOTP, WebAuthn/passkeys, recovery codes, and external providers can all be
steps in the ceremony before a browser session is issued.

The current `wevra.auth` package also contains placeholder modules and protocols
for challenges, TOTP credentials, WebAuthn credentials, and recovery codes.
Those are not yet concrete product capabilities. This change defines the
sub-specs needed to turn those reserved extension points into implementable
authentication features while keeping `wevra.auth` reusable and host-controlled.

Third-party OAuth in this change means OAuth/OIDC client login to external
providers such as Google, Apple, GitHub, Facebook, and LinkedIn. It is separate
from any future internal OAuth2/OIDC provider work.

## Goals / Non-Goals

**Goals:**

- Define concrete TOTP, recovery-code, WebAuthn/passkey, and third-party OAuth
  sub-specs.
- Keep all extended authentication methods attached to the canonical local user
  account rather than replacing it.
- Route every login method through the authentication ceremony and final session
  issuance boundary.
- Keep `is_active` and effective expiry checks as global eligibility gates for
  extended authentication.
- Define storage and service contracts in `wevra.auth`, with optional adapters
  behind the existing model-package and migration conventions.
- Keep host applications in control of feature enablement, product policy,
  templates, delivery, provider configuration, and route inclusion.
- Allow each authenticator type to be enabled, disabled, reset, revoked, or
  administratively managed without weakening the final-superuser or
  active-account invariants already introduced.

**Non-Goals:**

- Do not implement concrete TOTP, WebAuthn, OAuth, or recovery-code runtime
  code in this planning change.
- Do not select or add runtime dependencies until the implementation slice that
  actually uses them.
- Do not implement the internal OAuth2/OIDC authorisation provider in this
  change.
- Do not make external provider identity the canonical account record.
- Do not make templates or client-side UI the source of authentication policy.

## Decisions

### Model Login As A Ceremony With Method Assertions

The existing ceremony boundary should evolve from "authenticate then issue a
session" into "collect sufficient method assertions, then issue a session".
A method assertion is a successful proof such as:

- valid password for the local user;
- valid TOTP code for an active TOTP credential;
- valid recovery code consumed exactly once;
- valid WebAuthn authentication for a stored credential;
- successful external-provider callback for a linked or allowed provider
  identity.

The ceremony policy decides whether the collected assertions satisfy login for
the requested account and context. Session issuance remains the final step and
must not happen while a required challenge is outstanding.

Alternative considered: implement each authenticator as a separate login path
that writes sessions independently. That was rejected because it would duplicate
inactive-account checks, session issuance, return-target handling, and future
policy decisions.

### Keep Feature Exposure Host-Controlled

Each extended authentication capability should be gated by package options or
host-provided policy before any setup route, login choice, or callback endpoint
is exposed. Disabled capabilities should not appear in login ceremony choices
and should reject direct requests cleanly.

This matches the existing integration feature-flag abstraction and keeps
deployment risk low. A host can enable TOTP without enabling WebAuthn, or enable
Google and GitHub without enabling Facebook or LinkedIn.

### Use Package-Owned Stores With Optional ORM Adapters

`wevra.auth` should define stores for:

- challenge state;
- TOTP credentials;
- recovery-code sets;
- WebAuthn credentials;
- external provider identities.

The core services should depend on these protocols rather than direct
SQLAlchemy sessions where practical. SQLAlchemy ORM models can be supplied by
`wevra.auth.models` under the existing model-package metadata convention.

This keeps `wevra.auth` reusable while still allowing this application to use the
default SQLAlchemy adapter.

### Store Sensitive Credential Material Safely

Recovery codes must be generated as high-entropy one-time secrets and stored
only as verifiers, never as plaintext. Consuming a recovery code must be atomic
so the same code cannot succeed twice.

TOTP secrets are different: verification requires access to the seed. The store
contract should allow implementations to protect recoverable secrets, for
example through application-key encryption or a managed secret backend. The
specs should require plaintext TOTP seeds not to be exposed through APIs,
templates, logs, or management listings.

WebAuthn credential public keys are not secret, but credential IDs, user
handles, counters, transports, backup-state metadata, and device labels still
need careful lifecycle handling and should not be treated as arbitrary profile
data.

### TOTP Lifecycle

TOTP should have a pending enrolment state and an active credential state.
Starting enrolment creates a secret and display payload, but the credential
does not satisfy future login until the user confirms a valid code.

Disablement should require an authenticated account-management context and, by
policy, may require a recent password, another active factor, a recovery code,
or administrator action. Reset means invalidating the current active TOTP
credential so a new enrolment can begin; it is distinct from simply disabling
the credential when policy requires at least one usable second factor.

TOTP login verification should enforce time-window and replay policy. The
accepted time step/window should be configurable, but the defaults should favour
security over broad clock drift.

### Recovery Codes As Break-Glass Authenticators

Recovery codes should be issued in sets. Regenerating a set atomically revokes
the prior set. Each code can complete an advanced-authentication challenge once,
then becomes unusable.

Recovery codes are backup authenticators, not ordinary passwords. They should
not be displayed again after generation. The host UI should push users to save
them at generation time and warn when the remaining usable code count is low.

Administrative recovery policy must be explicit. For example, an administrator
may reset TOTP or WebAuthn credentials, but should not be able to retrieve
existing recovery codes.

### WebAuthn/Passkey Lifecycle

WebAuthn support should model registration and authentication as challenge
ceremonies tied to configured relying-party ID, origins, timeout, attestation
preference, and user-verification requirements.

Registration creates a pending challenge and only stores a credential after the
browser response is verified by a WebAuthn library. Authentication creates a
login challenge and accepts the assertion only after signature, origin,
challenge, RP ID, user-handle, and counter checks pass.

Credential revocation should be per credential. Users should be able to remove
lost devices, and administrators should be able to revoke credentials under
policy. Sign-count and clone-detection behaviour should be explicit: suspicious
counter regressions should fail authentication and surface a branchable result
for audit or account-protection policy.

Dependency decision: add a WebAuthn library only when this capability is
implemented. The design assumes a maintained library will perform protocol
verification; `wevra.auth` should not hand-roll WebAuthn cryptography.

### Third-Party OAuth Is Client Login, Not Internal Provider Work

Third-party OAuth should link external provider identities to local users.
The stable identity key is provider plus provider subject identifier, not email
alone. Provider email may help account creation or matching when policy allows,
but it must not by itself prove account ownership for linking.

Login through a provider should follow this order:

1. verify provider callback state and token response;
2. obtain provider subject and trusted claims;
3. resolve an existing linked local user, or apply account-creation/linking
   policy;
4. record a provider assertion in the authentication ceremony;
5. issue a session only when the ceremony policy is satisfied.

Linking an external provider to an existing account should require an
authenticated local user and should protect against linking a provider identity
already attached to another account. Unlinking should prevent users from
removing their last usable login/recovery path unless policy explicitly allows
administrative recovery.

Provider enablement should be per provider. Provider configuration should cover
client ID/secret, scopes, callback path, trusted issuer/discovery metadata where
applicable, and provider-specific claim mapping.

Dependency decision: Authlib is the likely OAuth/OIDC client implementation,
but it should be added only when concrete provider runtime code uses it.
FastAPI Users OAuth integrations can be reused where they fit, but the local
ceremony, linking policy, and canonical-user semantics remain `wevra.auth`
responsibilities.

### Route And Template Ownership Follows Module Web Composition

Extended authentication routes and default identity templates belong to
`wevra.auth`, but the application decides which route modules are enabled and can
override templates by logical path. This depends on the module route/context/
template handling change and should avoid building host-owned identity pages
for these flows.

### Results Must Remain Branchable

Extended authentication services should return branchable results with stable
error types rather than only booleans or framework exceptions. Expected result
types include invalid challenge, expired challenge, replayed code, disabled
method, missing credential, already linked provider, last usable method, and
inactive user.

This keeps CLI, HTML routes, JSON APIs, logs, and future audit hooks able to
handle security-sensitive failures consistently without leaking account state
through public responses.

## Risks / Trade-offs

- [Risk] TOTP seeds are recoverable secrets. -> Mitigation: require store
  contracts that do not expose plaintext outside verification/enrolment flows
  and allow encrypted or managed-secret storage adapters.
- [Risk] Recovery-code replay can happen under concurrent submissions. ->
  Mitigation: consume codes atomically through a store operation that succeeds
  once.
- [Risk] WebAuthn protocol verification is easy to implement incorrectly. ->
  Mitigation: use a maintained WebAuthn library when runtime implementation
  begins; do not hand-roll cryptographic verification.
- [Risk] External-provider account linking can create account takeover paths. ->
  Mitigation: link by provider subject, require authenticated linking for
  existing accounts, and never trust email-only matches without explicit policy.
- [Risk] Users can lock themselves out by disabling all usable methods. ->
  Mitigation: enforce a "last usable method" guard unless administrator policy
  provides an explicit recovery path.
- [Risk] Multiple authenticators can make login UX confusing. -> Mitigation:
  keep the ceremony result explicit about next allowed methods so UI can present
  choices rather than hard-coded branches.
- [Risk] Adding several capabilities in one planning change can blur
  implementation scope. -> Mitigation: keep the specs separate and implement in
  independent slices after this planning change lands.

## Migration Plan

1. Define the four new sub-specs: `totp`, `recovery-codes`, `webauthn`, and
   `third-party-oauth`.
2. Modify the existing `fastapi-users-auth-ext` and
   `identity-authentication` specs so the reserved hooks become concrete
   package contracts.
3. Keep runtime implementation deferred until each sub-spec has an
   implementation slice and dependency decision.
4. Update `identity-foundation` task `2.3` after these advanced authentication
   sub-specs exist and validate.
5. Implement capabilities incrementally, with migrations and dependencies added
   only in the slices that need them.

Rollback for this planning change is to leave the new sub-specs unapplied. Once
runtime implementations begin, each authenticator should remain independently
feature-gated so it can be disabled without removing the whole identity system.

## Open Questions

- Which concrete authenticator should be implemented first: TOTP, recovery
  codes, WebAuthn/passkeys, or a third-party OAuth provider?
- Which WebAuthn user-verification default should the first implementation
  require?
- Which third-party OAuth provider should be implemented first?
- Should external provider login be allowed to create accounts by default, or
  should first-time provider login require invitation/administrative approval?
- What exact policy should prevent unlinking or disabling the last usable login
  or recovery method?
