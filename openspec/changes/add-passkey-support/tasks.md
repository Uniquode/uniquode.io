## 1. Passkey Scope

- [ ] 1.1 Keep `webauthn` as a standalone requirement set under
  `specs/webauthn/spec.md`.
- [ ] 1.2 Define passkey feature enablement and relying-party config validation rules.
- [ ] 1.3 Define registration challenge and assertion challenge contracts.
- [ ] 1.4 Define credential storage and revocation requirements.
- [ ] 1.5 Define signature-counter/cloned-credential handling as branchable failure behaviour.

## 2. Integration

- [ ] 2.1 Ensure `identity-authentication` and `fastapi-users-auth-ext` consume
  passkey method assertions.
- [ ] 2.2 Keep Google/GitHub/Apple provider work out of this change.

## 3. Validation

- [ ] 3.1 Run `openspec validate add-passkey-support --strict`.
