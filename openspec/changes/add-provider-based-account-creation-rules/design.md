## Context

The provider callback path currently needs a strict decision boundary:
it must choose between linking, creating, or rejecting without allowing
implicit account takeovers.

## Goals / Non-Goals

**Goals:**

- Define deterministic provider-account creation policy in terms of provider, subject,
  claims, and host configuration.
- Define collision handling when a provider subject is already linked to another account.
- Keep policy outcomes explicit and auditable as branchable validation results.

**Non-Goals:**

- No Google/GitHub/Apple-specific claim parsing in this change.
- No passkey/TOTP implementation in this change.

## Decisions

### Canonical linking key

Provider identity lookup should use provider name plus provider subject identifier.
Email claims can inform policy but should not alone establish ownership.

### Create-or-link policy

Provider callback outcomes should be:
- linked provider identity -> resolve local account;
- unlinked + creation allowed -> create account per policy;
- otherwise reject with callback-safe failure.

### Explicit conflict guard

If a provider subject is already linked to a different account, linking should fail
unless there is an explicit reassignment policy.

## Migration Plan

1. Extract account-creation and linking-policy requirements into this change.
2. Keep external-identity model and provider linking flows in UT-173.
3. Keep provider-specific implementations (Google/GitHub/Apple) in their own changes.
4. Validate with focused policy and collision scenarios.
