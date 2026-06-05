## 1. Planning Artifacts

- [ ] 1.1 Create the `add-extended-authentication` proposal describing TOTP,
  recovery-code, WebAuthn/passkey, and third-party OAuth scope.
- [ ] 1.2 Create the design document that fixes the ceremony, storage,
  feature-gating, dependency, and account-linking architecture.
- [ ] 1.3 Keep runtime implementation, migrations, and dependency additions out
  of this planning change.

## 2. TOTP Sub-Spec

- [ ] 2.1 Add the `totp` spec covering explicit feature enablement.
- [ ] 2.2 Add TOTP enrolment and confirmation requirements with pending and
  active credential states.
- [ ] 2.3 Add TOTP login ceremony verification requirements, including inactive
  account rejection.
- [ ] 2.4 Add TOTP replay, time-window, disablement, reset, and secret-protection
  requirements.

## 3. Recovery-Code Sub-Spec

- [ ] 3.1 Add the `recovery-codes` spec covering generation of one-time backup
  codes.
- [ ] 3.2 Add verifier-only storage, non-redisplay, atomic consumption, and
  replay rejection requirements.
- [ ] 3.3 Add regeneration, revocation, remaining-count, and low-count status
  requirements.
- [ ] 3.4 Add last-usable-method protection for recovery-code revocation.

## 4. WebAuthn Sub-Spec

- [ ] 4.1 Add the `webauthn` spec covering feature enablement and relying-party
  configuration.
- [ ] 4.2 Add passkey registration challenge, browser response verification, and
  credential storage requirements.
- [ ] 4.3 Add WebAuthn login ceremony requirements, including inactive account
  rejection.
- [ ] 4.4 Add credential revocation, signature-counter update, clone-protection,
  and zero-counter policy requirements.

## 5. Third-Party OAuth Sub-Spec

- [ ] 5.1 Add the `third-party-oauth` spec covering per-provider enablement and
  provider configuration.
- [ ] 5.2 Add provider login ceremony requirements for linked users, policy-gated
  account creation, and inactive account rejection.
- [ ] 5.3 Add account linking requirements based on provider name and provider
  subject rather than email alone.
- [ ] 5.4 Add unlinking, provider identity lifecycle, provider token protection,
  callback state validation, and provider-specific claim mapping requirements.

## 6. Existing Capability Deltas

- [ ] 6.1 Modify `fastapi-users-auth-ext` to include concrete extended
  authentication storage, ceremony, TOTP, WebAuthn, recovery-code, and
  third-party OAuth contracts.
- [ ] 6.2 Modify `identity-authentication` so the canonical local-user ceremony
  supports concrete TOTP, recovery-code, WebAuthn/passkey, and linked provider
  assertions.
- [ ] 6.3 Preserve the distinction between third-party OAuth client login and
  any future internal OAuth2/OIDC provider work.

## 7. Validation And Follow-Up

- [ ] 7.1 Run `uv run openspec validate add-extended-authentication --strict`.
- [ ] 7.2 Review the advanced-authentication specs against ADR 0005 and ADR 0007
  for boundary drift.
- [ ] 7.3 Mark `identity-foundation` task 2.3 complete once the advanced
  authentication sub-spec planning is accepted.
- [ ] 7.4 Identify follow-up implementation slices for TOTP, recovery codes,
  WebAuthn/passkeys, and the first third-party OAuth provider.
