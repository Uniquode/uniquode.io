## 1. TOTP Scope

- [x] 1.1 Keep the `totp` spec as a standalone added-requirement set in
  `specs/totp/spec.md`.
- [x] 1.2 Add explicit tri-state TOTP mode (`disabled`, `opt_in`, `required`) to
  `wevra.auth` and wire it into ceremony policy.
- [x] 1.3 Model setup eligibility and bypass policy:
  - `opt_in` requires verified email to begin setup.
  - `required` prompts after login and after email verification when unset.
  - explicit bypass is honoured, but `required` re-prompts on next login.
- [x] 1.4 Add enrolment flow with pending -> active lifecycle and confirm step.
- [x] 1.5 Add login integration:
  - no TOTP code field by default.
  - HTMX-enhanced login decides whether to include code challenge or enrolment flow.
  - final login completion honours active TOTP/recovery assertions when required.
- [x] 1.6 Add recovery code generation, storage, and single-use consume semantics.
- [x] 1.7 Store TOTP seed material encrypted at rest using `crypt_`-prefixed persisted
  field/column names, and ensure no plaintext seed is persisted.
- [x] 1.8 Generalise Wevra secret key-ring environment names so all `crypt_` fields use
  universal current/legacy keys rather than provider-specific names.
- [x] 1.9 Store recovery codes only as non-plaintext one-way secret verifiers, without
  `crypt_` prefixes unless a reversible encrypted recovery-code field is explicitly added.
- [x] 1.10 Add replay/window policy, disablement, and reset behaviour, including
  required-mode prompts when credential is disabled.

## 2. Supporting Boundaries

- [x] 2.1 Ensure `identity-authentication` and `fastapi-users-auth-ext` capture TOTP as
  a first-class method assertion and policy input.
- [x] 2.2 Preserve existing password/login/session behaviour when `totp_mode` is
  `disabled`.
- [x] 2.3 Add tests for all enabled/disabled/required mode transitions and HTMX
  fragment responses.
- [x] 2.4 Add migration/model tests proving the persisted TOTP seed field uses the
  `crypt_` prefix and round-trips through encrypted storage.
- [x] 2.5 Add recovery-code storage tests proving recovery codes are transformed into
  one-way verifier fields and consumed once.

## 3. Validation

- [x] 3.1 Run `openspec validate add-totp-support --strict`.
- [x] 3.2 Add focused follow-up implementation slice references and link to this change:
  `identity-authentication` now exposes `AuthenticationAssertion`,
  `AuthenticationMethod`, and TOTP required-method helpers; `fastapi-users-auth-ext`
  storage protocols expose TOTP credential and recovery-code contracts for follow-up
  WebAuthn/passkey work without coupling those providers to this change.
