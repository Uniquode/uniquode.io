## Why

Linear: [UT-231](https://linear.app/uniquode/issue/UT-231/implement-google-authentication)

Google is a concrete third-party provider and should have its own integration slice
so its callback, claim mapping, and enablement rules can be defined and delivered
independently from other providers.

## What Changes

- Add Google-specific OAuth client configuration and callback handling.
- Define how provider assertions map into the local ceremony via the shared provider
  abstraction.
- Keep Google integration as concrete runtime work that consumes the shared account-linkage model
  and account-creation policy.

## Capabilities

### New Capabilities

- `google-authentication`: concrete Google provider enablement, callback handling,
  and local ceremony integration.

### Modified Capabilities

- `external-provider-account`: provider identity linking remains shared, while Google
  now contributes concrete provider assertions.
