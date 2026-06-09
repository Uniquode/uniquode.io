## 1. Rule Scope

- [ ] 1.1 Define a standalone `provider-account-creation-rules` spec in
  `specs/provider-account-creation-rules/spec.md`.
- [ ] 1.2 Define policy inputs (required claims, allow-list, domain or domain-like checks,
  and user-matching strategy where applicable).
- [ ] 1.3 Define collision, already-linked, and creation-denied outcomes as branchable
  authentication results.
- [ ] 1.4 Ensure provider callback flows separate creation and linking outcomes
  without conflating them.

## 2. Integration With Other Changes

- [ ] 2.1 Confirm alignment with UT-173 external identity and account-linkage contracts.
- [ ] 2.2 Make Google/GitHub/Apple slices depend on these policy outcomes.
- [ ] 2.3 Keep `identity-authentication` focused on canonical local account handling.

## 3. Validation

- [ ] 3.1 Run `openspec validate add-provider-based-account-creation-rules --strict`.
