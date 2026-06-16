## Why

Linear: [UT-211](https://linear.app/uniquode/issue/UT-211/add-email-backend)

Identity flows currently create verification and password-reset tokens through
application-owned delivery hooks, but the application has no concrete email
backend or operator configuration for sending those messages. This change adds
an async email delivery capability so identity flows can send actionable emails
without coupling `wybra.auth` to a specific provider.

## What Changes

- Add an async email backend built around `aiosmtplib` for SMTP delivery.
- Configure email delivery primarily through `EMAIL_URL`, including delivery
  type, credentials, host, port, and transport mode.
- Add settings support for email sender identity and any required safe defaults
  that are not naturally represented in the URL.
- Provide application wiring from configured email settings into the existing
  `IdentityDelivery` boundary.
- Add message rendering and front-end flow support for identity email events:
  email verification, password reset, future change-email confirmation, and
  future MFA reset flows.
- Keep FastAPI Users responsible for lifecycle token generation where it fits,
  while keeping transport, templates, and user-facing flow handling owned by the
  application/auth extension boundary.
- Add validation and documentation for supported email URL schemes, secret
  handling, and local/no-op behaviour.

## Capabilities

### New Capabilities

- `email-delivery`: Async email delivery configuration, SMTP transport,
  identity-event message rendering, and delivery integration through the
  application-owned `IdentityDelivery` boundary.

### Modified Capabilities

- `identity-authentication`: Expand account lifecycle email requirements from
  delivery hooks only to configured delivery for verification, password reset,
  and planned identity-security events such as change-email and MFA reset.
- `environment-configuration`: Add `EMAIL_URL` and related safe email settings
  to the supported environment-backed configuration and validation surface.

## Impact

- Adds `aiosmtplib` as a runtime dependency through `uv`.
- Affects `wybra.auth.delivery`, identity routes/templates, application settings,
  validation, and app startup wiring.
- Adds email configuration to operator documentation and example configuration.
- Introduces provider-neutral SMTP support that can be used with Fastmail or
  another SMTP provider without hard-coding provider-specific behaviour.
