## Context

Apple provider integration is a provider-specific authentication path with specific claims
and token lifecycle expectations.

## Goals / Non-Goals

**Goals:**

- Define explicit Apple provider configuration requirements.
- Define callback validation and claim handling for Apple assertions.
- Reuse shared identity-link and policy model from UT-173 and UT-230.

**Non-Goals:**

- No passkey or TOTP implementation.
- No change to provider account-creation policy; consume shared policy models.

## Decisions

### Separate provider implementation boundary

Apple integration stays as a dedicated provider slice for easier review and testing.

### Shared policy and model usage

Apple callback assertions should map into existing provider link records and must
not create a separate canonical identity model.
