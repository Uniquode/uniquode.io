## 1. TOTP Scope

- [ ] 1.1 Keep the `totp` spec as a standalone added-requirement set in
  `specs/totp/spec.md`.
- [ ] 1.2 Define explicit TOTP feature enablement and disablement controls.
- [ ] 1.3 Define pending/enabled/enforcement lifecycle for enrolment, confirmation, and login participation.
- [ ] 1.4 Define replay and time-window policy in contract terms, including inactive-account handling.
- [ ] 1.5 Define disablement and reset behaviour with no hidden last-method bypass by default.

## 2. Supporting Boundaries

- [ ] 2.1 Ensure `identity-authentication` and `fastapi-users-auth-ext` capture TOTP as a first-class method assertion.
- [ ] 2.2 Preserve existing password/login/session behaviour when TOTP is not enabled.

## 3. Validation

- [ ] 3.1 Run `openspec validate add-totp-support --strict`.
- [ ] 3.2 Add focused follow-up implementation slice references and link to this change.
