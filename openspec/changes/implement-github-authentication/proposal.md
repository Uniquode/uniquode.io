## Why

Linear: [UT-232](https://linear.app/uniquode/issue/UT-232/implement-github-authentication)

GitHub OAuth should be delivered as a dedicated provider slice so integration details,
claim handling, and callback policy are explicit and testable.

## What Changes

- Define GitHub provider enablement and callback handling.
- Define GitHub-to-local account mapping in the shared external identity model.
- Keep provider-specific logic scoped to GitHub and independent of other providers.

## Capabilities

### New Capabilities

- `github-authentication`: concrete GitHub provider login, linking, and callback handling.

### Modified Capabilities

- `external-provider-account`: add GitHub as an explicit provider implementation.
