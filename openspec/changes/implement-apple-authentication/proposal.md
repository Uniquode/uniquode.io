## Why

Linear: [UT-233](https://linear.app/uniquode/issue/UT-233/implement-apple-authentication)

Apple login requires provider-specific configuration and callback handling.
Implementing it as its own change keeps provider-specific concerns separate from shared provider policy.

## What Changes

- Add Apple provider enablement, configuration, and callback handling.
- Define Apple-specific claim mapping and local account resolution through the shared external identity model.
- Keep this change scoped to Apple runtime implementation and tests.

## Capabilities

### New Capabilities

- `apple-authentication`: concrete Apple OAuth/OIDC provider support.

### Modified Capabilities

- `external-provider-account`: add Apple as a concrete provider implementation that uses
  shared linking contracts.
