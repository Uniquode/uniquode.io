## 1. Google Scope

- [ ] 1.1 Keep Google OAuth as a provider-specific implementation set in
  `specs/google-authentication/spec.md`.
- [ ] 1.2 Define explicit Google config and enablement rules.
- [ ] 1.3 Define callback validation and state handling for Google login flow.
- [ ] 1.4 Define Google-linked account resolution and linking outcomes.
- [ ] 1.5 Ensure provider-specific token and claim handling follows shared secret-protection rules.

## 2. Validation

- [ ] 2.1 Run `openspec validate implement-google-authentication --strict`.
- [ ] 2.2 Ensure dependent changes (UT-173 and UT-230) are referenced for policy and linking contracts.
