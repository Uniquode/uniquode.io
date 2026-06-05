## Why

Linear: [UT-214](https://linear.app/uniquode/issue/UT-214/implement-auth-provider-runtime)
Parent: [UT-174](https://linear.app/uniquode/issue/UT-174/api-and-oauth2)
Depends on: `authorisation-model` capability, implemented by UT-213.

The repository now has an `auth_provider` package shell and accepted provider
contracts, but runtime OAuth2/OIDC provider behaviour is intentionally not yet
implemented. That deferral is still correct until group-managed scope
resolution exists. This change records the later runtime provider slice so the
contract-only state is visible in the backlog and can be advanced deliberately
after authorisation groups and scopes are available.

## What Changes

- Move `auth_provider` beyond contract-only scaffolding into runtime OAuth2/OIDC
  endpoint behaviour.
- Implement the required provider routes and services for client
  administration, authorisation grants, consent, token issuance, refresh-token
  rotation/reuse handling, introspection, and revocation.
- Use the accepted provider strategy already captured in the `auth-provider`
  spec: host-owned issuer/mount/lifetimes, RS256 access-token and ID-token
  defaults, opaque refresh tokens with non-recoverable verifiers, and
  host-provided subject/scope policy.
- Resolve allowed scopes through the group/scope authorisation foundation rather
  than storing group or flag logic inside `auth_provider`.
- Add Authlib or another protocol library only when endpoint implementation
  directly needs it and the design artifact has justified the dependency.

## Capabilities

### Modified Capabilities

- `auth-provider`: Implement runtime OAuth2/OIDC provider behaviour from the
  accepted contracts and token strategy.
- `api-access`: Use the provider runtime where local OAuth2 access tokens are
  required for machine-oriented APIs.
- `authorisation-model`: Supply scope policy for subject/client access
  decisions.

## Impact

- Affected areas include `auth_provider`, API authentication, token storage,
  refresh-token persistence, client/consent/grant stores, signing-key handling,
  authorisation group/scope resolution, validation, tests, and deployment
  documentation.
- This work is deliberately deferred until provider design binds to the
  existing group/scope authorisation model.
- Existing browser sessions and local identity flows must remain independent of
  local OAuth2 provider runtime behaviour unless a route explicitly requires API
  token semantics.
