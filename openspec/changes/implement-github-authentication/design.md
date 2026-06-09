## Context

GitHub OAuth is a separate third-party provider implementation with its own
client and claim profile.

## Goals / Non-Goals

**Goals:**

- Define explicit GitHub provider configuration and scope requirements.
- Define provider callback validation and safe claim mapping.
- Reuse shared provider-linked identity contracts without changing account-creation policy.

**Non-Goals:**

- No Google-specific claim handling in this change.
- No TOTP or passkey implementation in this change.

## Decisions

### Provider-specific implementation path

GitHub implementation should remain isolated behind per-provider code and tests,
while still using common provider assertion and linking contracts.

### Claim handling

GitHub claim mapping and username/email interpretation is provider-specific and
must not be shared as a default for other providers.
