## Why

[UT-236](https://linear.app/uniquode/issue/UT-236/add-sms-email-verification)

Users need recovery and step-up verification paths that do not depend on an already-enrolled authenticator. Email and SMS verification codes provide practical recovery, onboarding, and sensitive-action confirmation options while preserving stronger MFA methods as the preferred authentication posture.

## What Changes

- Add verification-code delivery channels for `email_code` and `sms_code`.
- Support verification-code ceremonies for normal login step-up, password reset verification, lost authenticator recovery, sensitive account operation confirmation, and future account recovery flows.
- Treat email and SMS codes as weaker factors than TOTP and WebAuthn because mailbox compromise, SIM swap, SMS interception, number recycling, and phone-number compromise are realistic threats.
- Require lost-authenticator flows to start an explicit recovery ceremony rather than silently disabling MFA or bypassing stronger factor requirements.
- Store verification codes only as one-way verifiers, never plaintext.
- Use a provider-driver abstraction for SMS delivery where a configured class implements an internal protocol.
- Add configuration for the selected SMS driver class and driver-specific configuration data.
- Require SMS providers to support AU-compliant registered alphanumeric sender IDs / sender-name registration, not merely SMS sending.
- Preserve encrypted-at-rest handling for persisted provider credentials and reversible provider secrets.

## Capabilities

### New Capabilities

- `verification-code-delivery`: Defines email and SMS verification-code channels, code lifecycle requirements, delivery provider abstractions, and the security posture for out-of-band verification ceremonies.

### Modified Capabilities

- `identity-authentication`: Adds verification-code ceremonies as supported step-up, password reset verification, sensitive-operation confirmation, and account recovery mechanisms.
- `totp`: Adds lost-authenticator recovery behaviour that can use email/SMS verification ceremonies without silently disabling MFA.
- `environment-configuration`: Adds configuration requirements for selecting an SMS delivery driver by class name and providing driver-specific configuration data.
- `crypto-service`: Clarifies that persisted provider credentials and reversible SMS/email delivery secrets remain encrypted at rest, while verification codes are stored as one-way verifiers.

## Impact

- Authentication flow orchestration will need to support out-of-band verification ceremonies alongside existing password, TOTP, and session assertions.
- Email delivery will depend on the planned complete email sending backend.
- SMS delivery will require a provider-driver interface and at least one concrete driver implementation or test driver.
- Configuration will need a provider section for driver class selection and driver-specific data.
- SMS provider selection must account for Australian sender-name compliance, especially registered alphanumeric sender IDs / alpha tags.
- Tests should cover Wevra-owned verification behaviour in Wevra, with host applications testing only their own configuration and composition wiring.
