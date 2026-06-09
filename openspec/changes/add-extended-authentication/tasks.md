## 1. Scope Definition

- [x] 1.1 Keep this change focused on external identity and account-linkage
  contracts for UT-173.
- [x] 1.2 Move TOTP, recovery-code, passkey, and provider-implementation
  details to dedicated changes (UT-228, UT-229, UT-230, UT-231, UT-232, UT-233).

## 2. External Identity

- [x] 2.1 Define external provider identity storage and canonical link requirements
  in `specs/external-identity/spec.md`.
- [x] 2.2 Define how existing linked provider identities are resolved into local
  user accounts before final ceremony completion.
- [x] 2.3 Define account-linking and unlinking flows, including last-usable
  method protections at link lifecycle boundaries.
- [x] 2.4 Define feature flags in shared wevra auth settings for provider,
  TOTP, and passkey enablement.

## 3. Shared Boundaries

- [x] 3.1 Update `fastapi-users-auth-ext` contracts for external-provider
  linking, callback state, and provider identity lifecycle.
- [x] 3.2 Update `identity-authentication` so provider assertions can be used
  by the authentication ceremony through the local-user model.

## 4. Validation

- [x] 4.1 Run `openspec validate add-extended-authentication --strict`.
- [x] 4.2 Ensure follow-on changes reference UT-173 as their shared linkage
  dependency:
  - `UT-228`, `UT-229`, `UT-230`, `UT-231`, `UT-232`, `UT-233`.
