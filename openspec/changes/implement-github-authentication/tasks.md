## 1. GitHub Scope

- [ ] 1.1 Keep GitHub OAuth as a provider-specific implementation set in
  `specs/github-authentication/spec.md`.
- [ ] 1.2 Define GitHub configuration and callback validation requirements.
- [ ] 1.3 Define GitHub claim mapping and local account linkage outcomes.
- [ ] 1.4 Keep provider-specific runtime code isolated from Google/Apple slices.
- [ ] 1.5 Validate failure modes for invalid state, invalid token, and already-linked identities.

## 2. Validation

- [ ] 2.1 Run `openspec validate implement-github-authentication --strict`.
- [ ] 2.2 Align with UT-173 and UT-230 for external identity contracts and account-creation policy.
