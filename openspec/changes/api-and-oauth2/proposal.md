## Why

Linear: [UT-174](https://linear.app/uniquode/issue/UT-174/api-and-oauth2)
The application has a browser-session identity foundation and planned
external-provider authentication work, but it does not yet have a coherent
machine-oriented API access model. This change defines the API and OAuth2 slice
so browser sessions, API tokens, upstream OAuth2 login/linking, and any future
local OAuth2 authorisation capability have clear boundaries before
implementation work begins.
Local OAuth2/OIDC provider runtime remains deliberately unimplemented until a
concrete API, federation, or delegated-access requirement justifies it.

## What Changes

- Establish API token support for machine access to application APIs.
- Clarify the boundary between browser sessions and API authentication.
- Decide whether local OAuth2 authorisation-server capability is required, and
  if so define it from the concrete API or federation use case rather than from
  a dormant package shell.
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
- `oauth2-authorisation`: Future local OAuth2/OIDC authorisation-provider
  behaviour if the API slice identifies a delegated-access requirement.

### Modified Capabilities

- `identity-authentication`: Clarify how browser sessions, local users, and
  external-provider identities relate to API access.
- `third-party-oauth`: Align upstream provider login/linking with API and local
  OAuth terminology.

## Impact

- Affected areas include API route authentication, identity session boundaries,
  token storage, scope/client policy, validation, and operator documentation.
- Concrete OAuth/OIDC runtime dependencies must remain requirement-scoped and
  should be selected during the design artifact.
- Local OAuth/OIDC provider runtime endpoints should remain deferred unless the
  API design proves they are needed beyond scoped API keys or server-side
  sessions.
- Existing browser login, session resolution, and identity management behaviour
  must remain compatible.
