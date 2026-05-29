# 0007: Internal OAuth Provider and Token Strategy

Date: 2026-05-29

Status: Provisional

## Context

The project expects future OAuth2/OIDC provider capability for API consumers and
integrations. This capability is separate from browser-session authentication,
advanced authentication factors, and OAuth client login through external
providers.

ADR 0005 separates the future internal provider behind an internal OAuth
provider boundary. ADR 0006 establishes that groups, flags, scopes, and
route/API policy belong to the authorisation model, while the provider consumes
that policy through explicit interfaces.

The provider must be reusable and FastAPI-oriented, but it must not depend on
`uniquode`, FastAPI Users, or the `auth_ext` advanced-authentication package.

## Decision

Use `auth_provider` as the Python import package for the internal provider
boundary. Use this name consistently when referring to the code and module
boundary.

If prepared for publication, use `fastapi-oauth-provider` as the distribution
name. This reflects the FastAPI routing/runtime target without implying a hard
dependency on FastAPI Users or `auth_ext`.

Keep `auth_provider` as a sibling package to `auth_ext`. The host application
composes both packages and adapts identity/session state into provider
interfaces where required.

Make provider route exposure host-controlled. The host decides whether the
provider is enabled and where it is mounted. The provider defines routes
relative to its root, while the host supplies the public issuer and mount
context needed to generate endpoint metadata.

Do not hard-code issuer, audience, mount path, token lifetimes, supported
grants, client data, consent policy, or scope meanings in the provider package.
Those values are supplied through options and host/provider interfaces.

Use Authlib for OAuth2/OIDC protocol machinery when runtime provider
implementation begins. Do not add Authlib before provider code directly uses it.

Use asymmetric signing keys for JWT access tokens and OIDC ID tokens. The
default signing algorithm should be `RS256` because it is the most broadly
supported JWT algorithm across OAuth2/OIDC clients, resource servers, and API
gateways.

Publish public verification keys through JWKS. JWKS contains public key material
and key metadata such as `kid`, `kty`, `alg`, and `use`; it does not encode
issuer, audience, or authorisation policy. Clients must verify signatures using
JWKS and then separately validate claims such as `iss`, `aud`, `exp`, `nbf`,
and scopes.

Serve discovery and JWKS over HTTPS. Ordinary public TLS, such as Let's Encrypt,
is sufficient for transport trust. JWKs do not need CA or notary signatures.

Use short-lived JWT access tokens and opaque server-stored refresh tokens by
default. Refresh tokens should be high-entropy random values. Store only a
server-side verifier, such as a keyed hash of the token value, rather than the
plaintext token. Plaintext refresh tokens must not be recoverable from the
database.

Treat refresh tokens as single-use within a token family. A successful refresh
invalidates the presented token and issues a successor. Reuse of an invalidated
refresh token should be treated as a compromise signal and should revoke or
quarantine the token family so callers cannot continue rotating stolen tokens.

## Consequences

Keeping `auth_provider` separate avoids coupling delegated authorisation and
token issuance to identity lifecycle and advanced-authentication concerns.

The provider can be reused by FastAPI applications that do not use FastAPI
Users, while `uniquode` can still adapt `auth_ext` sessions into provider
subject resolution.

Host-owned mounting keeps public URL layout configurable. Provider metadata must
therefore receive issuer and mount context explicitly rather than inferring it
from internal stripped paths.

RS256 is less compact and slower than ES256 or EdDSA, but it maximises
interoperability for the initial provider. ES256 and EdDSA/Ed25519 remain future
optional algorithms if consumers require them.

Opaque refresh tokens require server-side persistence, but they support
immediate revocation, reuse detection, token-family rotation, and user/client
state checks. They also keep signing-key rotation tied to short-lived JWT
lifetimes rather than long refresh-token lifetimes.

Signing-key rotation is an operational process. The provider should sign new
JWTs with one active key while continuing to publish old public keys in JWKS
until all JWTs signed by them have expired, plus clock-skew, JWKS cache, and
operational safety margins.

## Open Questions

- Whether the first implementation should support OAuth2 only or include OIDC
  discovery and ID tokens immediately.
- Which grants should be implemented first.
- How client registration and secret rotation should be administered.
- How consent should be represented for first-party versus third-party clients.
- Whether scopes become first-class database records or remain policy-level
  strings mapped from groups and flags.
- Whether ES256 or EdDSA should be supported in the first production provider
  release after RS256.

## Follow-Up Work

- Define `auth_provider` protocol/dataclass interfaces for subjects, clients,
  grants, tokens, consent, scopes, audiences, and signing keys.
- Define host settings for provider enablement, issuer, and mount path.
- Define authorisation scope policy in the authorisation model.
- Add Authlib when runtime OAuth2/OIDC endpoint implementation begins.
- Define key generation, storage, rotation, JWKS publication, and emergency key
  revocation operator workflows.
