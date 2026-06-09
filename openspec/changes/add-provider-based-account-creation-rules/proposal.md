## Why

Linear: [UT-230](https://linear.app/uniquode/issue/UT-230/add-provider-based-account-creation-rules)

Provider callbacks and linking currently depend on clear account-creation policy.
Without an explicit policy, callback outcomes are ambiguous and can produce unsafe or
inconsistent account outcomes.

## What Changes

- Define provider-based account-creation rules in a dedicated authentication
  requirement set.
- Define conflict handling for provider identity collisions and explicit acceptance
  criteria when no local account exists.
- Preserve the canonical local user account model while adding provider identity
  creation pathways.

## Capabilities

### New Capabilities

- `provider-account-creation-rules`: explicit policy for creating local accounts
  from external provider assertions.

### Modified Capabilities

- `identity-authentication`: keep local user as the canonical subject while handling
  external provider callbacks according to explicit policy.
- `third-party-oauth` flows: require policy checks before account creation.

## Impact

- Clarifies when `callback -> local account` creation is legal and auditable.
- Enables provider-specific implementations (Google/GitHub/Apple) to share one policy model.
