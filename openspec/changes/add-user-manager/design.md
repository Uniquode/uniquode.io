## Context

The identity foundation establishes local users, an `admin-created` account
creation policy, SQLAlchemy async persistence, Alembic migrations, FastAPI Users
integration, and application-owned browser identity routes. That leaves a
practical operations gap: local administrators need a way to manage users before
there is a dedicated browser-based admin surface.

The CLI should not depend on an API token model that does not exist yet. An
API-backed user-management mode will become more relevant after the API and
authorisation foundations define administrative scopes and tokens.

## Goals / Non-Goals

**Goals:**

- Add a reusable `auth_ext`-owned `usermgr` script.
- Provide create, update, delete, deactivate, list, and password-change
  operations.
- Support explicit creation of admins and superusers.
- Support useful list filters and ordering.
- Use the existing reusable `auth_ext` identity service boundaries directly.
- Keep destructive operations deliberate and visible.
- Keep command output scriptable enough for operators and tests, including JSON
  and CSV formats.

**Non-Goals:**

- Build a browser-based user-management UI.
- Introduce an admin API token model before the API/authorisation foundation.
- Add role/group/permission editing before the authorisation foundation exists.
- Implement OAuth account linking or advanced-authentication credential
  management.

## Decisions

### Use direct service access first

The first `usermgr` implementation will be owned by `auth_ext` and operate
directly against the configured identity database and FastAPI Users identity
services.

It must not depend on a host application project root, host settings object, or
`uniquode` modules. It loads generic auth configuration from `--config`,
`AUTH_CONFIG`, or `./auth.toml` when present. Configuration lives under an
`[auth]` table so host applications can share the same source rather than
wrapping the CLI:

```toml
[auth]
database_url = "sqlite+aiosqlite:///identity.sqlite3"
session_cookie_secure = false
```

Relative SQLite database paths are resolved relative to the `auth.toml` file
directory. `AUTH_DATABASE_URL` may override the configured database URL for
automation.

Rationale: the application does not yet have an administrative API token/scope
model. Building an API-backed CLI now would require inventing admin token policy
ahead of the API and authorisation foundations.

Future direction: once API tokens and administrative scopes exist, a later
change can add an API-backed mode that authenticates with an admin token and
uses server endpoints instead of direct database access.

### Distinguish admins from superusers

The current identity model inherits FastAPI Users' `is_superuser` field.
FastAPI Users may care about that flag, and the application should treat it as
absolute privilege. Superusers should be rare, but there must always be at
least one.

This slice should also add an application-owned `is_admin` flag. It defaults to
`False` and represents enhanced administrative capability, not absolute
superuser control. It is intentionally separate from `is_superuser` so the
project can build ordinary administration around admins without overusing
superusers.

Future roles, groups, or permissions should be defined by the authorisation
foundation. `is_admin` is the coarse application-level administration marker
until that richer policy exists.

### Keep account creation policy explicit

`usermgr create` is a controlled administrative path and does not imply open
public registration. The command should make admin and superuser creation
explicit through `--admin` and `--superuser`. A superuser may also be an admin,
but the flags remain distinct.

`usermgr create` should also accept the user metadata fields introduced in this
change:

- `--display-name`
- `--preferred-name`
- `--timezone`
- `--expires-at`

### Require safe password input

User creation and password changes should prompt for password entry and
confirmation by default, without echoing values, using Python's standard
non-echoing password input support. The CLI should also support
`--password -`, which reads one password value from stdin for operator
automation and skips confirmation. It should not accept a plain command-line
password value that is likely to leak through shell history or process listing.

### Keep password policy injectable

Password validation belongs at the reusable `auth_ext` identity boundary, not
inside the host application or the `usermgr` command. `IdentityOptions` should
accept a password policy object with two operations:

- `strength(password, user=None)`: returns a score, label, and feedback that a
  future UI can use for a strength gauge while a user types.
- `validate(password, user=None)`: returns a branchable `Result` outcome used
  by user creation, password reset, and user-management password changes.

The default policy should reject blank, too-short, and materially weak
passwords while remaining a replaceable baseline. Its minimum length, minimum
strength score, minimum character-category count, and common-fragment list
should be settings-owned so operators can tune the default policy through
generic `[auth.password.policy]` configuration. A host can also supply a
stricter policy object that requires punctuation, external breach checks, or
other local requirements without changing the CLI.

### Create verified accounts by default

Operator-created users should default to `is_verified=True`, because the
operator is explicitly provisioning the account. `usermgr create --unverified`
should be
available when the operator wants the user to complete the email-token
verification flow.

Unverified accounts should carry enough metadata for future cleanup/resend
policy. The user model should record when a verification email was sent. A
later application service can use that value to avoid repeated sends, resend
when policy allows, or expire unverified accounts after a configured age.

### Store operational timestamps as Unix timestamp floats

The user model must add float timestamp fields using Unix seconds. This is an
explicit application requirement and is not an implementation detail to replace
with `DateTime`, integer timestamps, or database-native timestamp columns in
this change.

- `created_at`: set when the account is created.
- `modified_at`: updated when account management changes the account.
- `last_login_at`: updated when authentication finalisation succeeds, and later
  when authenticated API use has an associated user identity.
- `expires_at`: nullable; when non-null, the account is effectively inactive at
  or after that Unix timestamp.
- `email_verification_sent_at`: nullable; set when a verification email is sent.

Using timestamp floats keeps CLI filtering and serialisation straightforward and
matches the operator-facing timestamp contract for this slice. The design does
not depend on sub-second equality; boundary-sensitive checks such as expiry use
strict less-than/greater-than comparisons against UTC Unix seconds. Numeric
operator input is interpreted as Unix seconds. Non-numeric timestamp input
accepted by the CLI is parsed through `dateparser` before being stored or used
for comparisons. All values are UTC instants; presentation can apply the user's
preferred timezone.

Stored `is_active` remains the manual account-state flag. Effective account
activity is `is_active` and not expired. Identity checks and `--active` list
filtering should use this effective activity so an account with a non-null
`expires_at` automatically stops being treated as active once the timestamp is
reached, without requiring a background job to rewrite `is_active`.

### Store simple user profile metadata

The user model should add nullable `display_name` and `preferred_name` text
fields. `display_name` is the longer user-facing name. `preferred_name` is the
short name, given name, handle, or common name the application can use when
addressing the user.

`usermgr create` and `usermgr update` should support `--display-name` and
`--preferred-name`. These fields do not need defaults. Application presentation
may derive a fallback preferred name, such as the local part of the email
address, when `preferred_name` is unset.

### Store a preferred timezone

The user model should add a nullable `preferred_timezone` string. `None` means
unspecified. When a user has no stored preference, runtime presentation falls
back to the current server/application timezone. The CLI should not persist a
timezone unless the operator supplies a user preference.

Stored timezone preferences should be stable IANA timezone identifiers. The
runtime server fallback is not copied into each user row. Validation uses the
host Python `zoneinfo` database, so deployments should provide current tzdata
when the operating system does not ship it.

### Resolve user targets predictably

Commands that operate on one user should accept a single target argument.
Targets containing `@` are resolved as syntactically valid email addresses.
Malformed email targets fail as invalid input instead of being reported as
missing users. Non-email targets are resolved as user IDs using the current
identity model's ID format; malformed IDs likewise fail as invalid input. The
current model uses UUID user IDs, but the command contract should not require
an extra `--id` flag if the target is clearly not an email address.

### Treat delete as destructive

`usermgr delete` should require a positive confirmation unless a deliberate
force option is provided. Deletion should identify the target user clearly
before removal.

Superusers must not be deleted through `usermgr delete`. If removing a
superuser account is required, the account must first cease being a superuser
through a dedicated flag-management path.

### Treat deactivate as non-destructive

`usermgr deactivate` should set the existing account inactive without removing
the row. Deactivation should also identify the target user clearly. Existing
session handling should continue to reject inactive users through the identity
boundary.

Superusers must not be deactivated through `usermgr deactivate`. If disabling a
superuser account is required, the account must first cease being a superuser
through a dedicated flag-management path. Future superuser flag changes must
preserve at least one superuser account and reject attempts to remove the final
superuser flag.

### Update user attributes through one command

`usermgr update TARGET` should support focused changes to existing user
attributes:

- `--admin` / `--no-admin`
- `--superuser` / `--no-superuser`
- `--verify` / `--no-verify`
- `--password` for an interactive password prompt
- `--password -` for one password read from stdin
- `--display-name`
- `--no-display-name`
- `--preferred-name`
- `--no-preferred-name`
- `--timezone`
- `--no-timezone`
- `--expires-at`
- `--no-expires-at`

Updating password through `usermgr update` should follow the same session
revocation behaviour as the password-change command: revoke existing sessions
by default, with `--no-revoke` to preserve them.

Removing the superuser flag must be rejected when the target is the sole
superuser account.

### Revoke sessions on password change by default

`usermgr password` should revoke existing user sessions by default after a
successful password change. Operators can preserve sessions with an explicit
`--no-revoke` option when that is the intended operational outcome.

### Model list sorting around available fields

This change should add the fields needed for list filtering and ordering rather
than exposing unsupported switches. List sorting should support:

- `email`: full email address, ascending by default.
- `email-domain`: domain after `@`, then full email as a stable tie-breaker.
- `created-at`: creation timestamp, descending by default.
- `modified-at`: modification timestamp, descending by default.
- `last-login-at`: last successful authentication timestamp, descending by
  default.

### Support explicit list filters

List filtering should support:

- email pattern matching with `*` as the only wildcard.
- domain pattern matching against the part after `@`, with `*` as the only
  wildcard.
- `--admin`/`--non-admin`, `--superuser`/`--non-superuser`,
  `--active`/`--inactive`, and
  `--verified`/`--unverified` filters.
- since/before ranges for created, modified, and last-login timestamps.

The CLI should escape SQL wildcard characters in operator input and translate
only `*` to the backend wildcard form.

Timestamp filter input should be operator-friendly. The implementation must
parse numeric Unix timestamp values directly before trying `dateparser`; this
means digit-only values such as `20250101` are Unix seconds, and calendar dates
should use separated forms such as `2025-01-01`. Non-numeric input should use
`dateparser` rather than maintaining a narrow handwritten parser. It should
accept ISO 8601 variants with `T` or space separators, and practical
natural-language values such as "last week", "last month", "last year", and
named dates when `dateparser` supports them.

`dateparser` should be configured deliberately for operator input rather than
left entirely implicit. The initial parser settings should prefer Australian/UK
date ordering where ambiguous (`DMY`), resolve relative dates against the
current runtime timezone context reported by Python, falling back to UTC when a
stable IANA timezone key is unavailable, and normalise parsed results to UTC
Unix timestamp floats before filtering.

Date range long options should have compact short aliases:

- `-C` / `--since-created-at`
- `-c` / `--before-created-at`
- `-M` / `--since-modified-at`
- `-m` / `--before-modified-at`
- `-L` / `--since-last-login-at`
- `-l` / `--before-last-login-at`

Uppercase means the lower bound; lowercase means the upper bound for the same
timestamp field.

### Provide scriptable output formats

The default output should be human-readable line or table output. `--json`
should emit JSON suitable for scripts, and `--csv` should emit standard CSV.
JSON and CSV output should not include password material. Human-readable list
output and CSV should serialise timestamps as ISO 8601 strings. JSON may retain
numeric Unix timestamp values to preserve machine-readable precision. JSON
output should omit fields whose values are `None` rather than emitting noisy
`null` values.

## Risks / Trade-offs

- [Risk] Direct database access bypasses API-level policy. Mitigation: treat
  `usermgr` as an auth-package local/operator tool and keep API-backed remote
  administration deferred until scopes and tokens exist.
- [Risk] CLI operations can become unsafe for production data. Mitigation:
  require explicit database configuration, confirmations for destructive
  commands, and tests around command behaviour.
- [Risk] Listing requirements may outpace stored metadata. Mitigation: implement
  available filters first and make unavailable fields explicit rather than
  silently incorrect.

## Migration Plan

1. Add `usermgr` project script targeting `auth_ext.usermgr`.
2. Add command parser, command dispatch module, and generic `[auth]`
   configuration loading from `auth.toml`.
3. Add user create command using identity/FastAPI Users services.
4. Add user update command for verification status, admin status, superuser
   status, password, display name, preferred name, expiry, and preferred
   timezone.
5. Add user delete command with confirmation/force behaviour.
6. Add user deactivate command.
7. Add user list command with email/domain/status/date filters and supported
   ordering.
8. Add password change command with interactive confirmation, `--password -`
   stdin input, and session revocation controls.
9. Add JSON and CSV output modes.
10. Add tests for all command behaviours and failure paths.
11. Update validation or documentation if a command smoke check becomes useful.

## Open Questions

- None currently identified.
