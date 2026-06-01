## Why

Linear: [UT-174](https://linear.app/uniquode/issue/UT-174/api-and-oauth2)
Related runtime provider change:
[UT-214](https://linear.app/uniquode/issue/UT-214/implement-auth-provider-runtime)

The application has a browser-session identity foundation, reserved internal
OAuth provider contracts, and planned external-provider authentication work, but
it does not yet have a coherent machine-oriented API access model. This change
defines the API and OAuth2 slice so browser sessions, API tokens, upstream
OAuth2 login/linking, and any local OAuth2 authorisation capability have clear
boundaries before implementation work begins.
Local OAuth2/OIDC provider runtime implementation is split into
`implement-auth-provider-runtime` and remains blocked on group-managed scope
resolution from `add-group-management`.

## What Changes

- Establish API token support for machine access to application APIs.
- Clarify the boundary between browser sessions and API authentication.
- Define the required local OAuth2 authorisation-server capability, including
  how it relates to the existing `auth_provider` contracts and the deferred
  provider runtime implementation change.
- Clarify how upstream third-party OAuth integrations participate in login and
  account-linking without becoming the canonical local identity.
- Define API route authentication and authorisation expectations for human,
  service, and future OAuth client callers.
- Keep token, scope, consent, client, and grant policy host-owned where product
  authorisation requirements are not yet settled, and resolve scopes through the
  authorisation group foundation once it exists.

## Capabilities

### New Capabilities

- `api-access`: Machine-oriented API authentication, API token lifecycle, and
  request authentication policy.
- `oauth2-authorisation`: Local OAuth2/OIDC authorisation-provider behaviour
  built on the existing `auth_provider` boundary.

### Modified Capabilities

- `auth-provider`: Move from contract-only provider scaffolding toward the
  minimum runtime authorisation-server behaviour required by the API slice.
- `identity-authentication`: Clarify how browser sessions, local users, and
  external-provider identities relate to API access.
- `third-party-oauth`: Align upstream provider login/linking with API and local
  OAuth terminology.

## Impact

- Affected areas include API route authentication, `auth_provider`, identity
  session boundaries, token storage, scope/client policy, validation, and
  operator documentation.
- Concrete OAuth/OIDC runtime dependencies must remain requirement-scoped and
  should be selected during the design artifact.
- Auth-provider runtime endpoints should be deferred to
  `implement-auth-provider-runtime` until group/scope authorisation exists.
- Existing browser login, session resolution, and identity management behaviour
  must remain compatible.
