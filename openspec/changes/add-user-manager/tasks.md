## 1. Command Contract

- [x] 1.1 Add `usermgr` to project scripts, targeting `auth_ext.usermgr`.
- [x] 1.2 Add command parser and dispatch for `create`, `update`, `delete`, `deactivate`, `list`, and `password` or equivalent password-change command.
- [x] 1.3 Keep command implementation async-compatible with the identity persistence boundary.
- [x] 1.4 Add human-readable, JSON, and CSV output modes where command output lists user data, with JSON omitting fields whose values are `None`.
- [x] 1.5 Add `dateparser` as the runtime dependency for flexible CLI timestamp parsing.
- [x] 1.6 Add generic `[auth]` configuration loading from `auth.toml` /
  `AUTH_CONFIG`, with `AUTH_DATABASE_URL` override support.

## 2. User Model Metadata

- [x] 2.1 Add Unix timestamp float fields for `created_at`, `modified_at`, `last_login_at`, `expires_at`, and `email_verification_sent_at`.
- [x] 2.2 Add `is_admin`, defaulting to false and distinct from `is_superuser`.
- [x] 2.3 Add nullable `display_name` and `preferred_name`.
- [x] 2.4 Add nullable `preferred_timezone`; leave it unset by default and use server/application timezone only as a runtime presentation fallback.
- [x] 2.5 Add a migration for the new user metadata fields.
- [x] 2.6 Update authentication finalisation so successful user-associated authentication updates `last_login_at`.
- [x] 2.7 Update identity active-user checks so non-null expired accounts are treated as inactive without rewriting `is_active`.
- [x] 2.8 Update verification-email delivery flow so sending a verification email records `email_verification_sent_at`.
- [x] 2.9 Add indexes for user-management filtering and ordering fields.

## 3. User Operations

- [x] 3.1 Implement user creation through the existing identity/FastAPI Users services.
- [x] 3.2 Add explicit admin and superuser options for create.
- [x] 3.3 Default operator-created users to verified, with an explicit unverified option.
- [x] 3.4 Implement duplicate-user handling with a clear non-zero failure.
- [x] 3.5 Implement create options for display name, preferred name, expiry, and preferred timezone.
- [x] 3.6 Implement target resolution by email when the target contains `@`, otherwise by current user ID format.
- [x] 3.7 Implement safe password input through hidden prompts and `--password -` stdin input.
- [x] 3.8 Implement user update for admin status, superuser status, verification status, password, display name, preferred name, expiry, and preferred timezone, including explicit clear options for nullable metadata.
- [x] 3.9 Reject removal of the final superuser flag.
- [x] 3.10 Implement hard deletion with confirmation and a deliberate force option.
- [x] 3.11 Reject deletion and deactivation of superuser accounts.
- [x] 3.12 Implement user deactivation by setting the account inactive without deleting the row.
- [x] 3.13 Implement user listing with email, email-domain, admin, superuser, active, and verified filters.
- [x] 3.14 Implement created, modified, and last-login since/before filters with long and short flags.
- [x] 3.15 Implement flexible timestamp parsing by handling numeric Unix timestamps directly, then using `dateparser` for ISO 8601 variants and supported natural-language date/time strings.
- [x] 3.16 Implement supported list ordering for email, email domain, created, modified, and last-login fields.
- [x] 3.17 Implement interactive password change with hidden password entry and confirmation.
- [x] 3.18 Implement password-change session revocation by default, with an explicit no-revoke option.
- [x] 3.19 Add an injectable password policy boundary with strength scoring and Result-based validation.

## 4. Safety and Documentation

- [x] 4.1 Document that the initial CLI uses local service/database access rather than an admin API token.
- [x] 4.2 Document that API-backed operation is deferred until administrative API tokens/scopes exist.
- [x] 4.3 Ensure destructive operations identify the target user clearly before proceeding.
- [x] 4.4 Document password input modes and the default password-change session revocation behaviour.
- [x] 4.5 Document admin/superuser update semantics, superuser deletion/deactivation protections, and the preferred-timezone fallback semantics.

## 5. Validation

- [x] 5.1 Add focused tests for command parser and dispatch.
- [x] 5.2 Add focused tests for create, create-admin, create-superuser, create-unverified, duplicate create, update, delete, deactivate, target resolution, list filters, output formats, and password change.
- [x] 5.3 Add tests for confirmation, `--password -` stdin input, mismatch failure paths, and session revocation controls.
- [x] 5.4 Add tests for superuser demotion, deletion, and deactivation protection.
- [x] 5.5 Add tests for user metadata defaults, effective expiry handling, timestamp updates, JSON null-field omission, flexible timestamp parsing, and timestamp range filtering.
- [x] 5.6 Run `uv run ruff format --check`, `uv run ruff check`, `uv run ty check src/`, `gtimeout 30s uv run pytest`, and `uv run openspec validate add-user-manager --strict`.
