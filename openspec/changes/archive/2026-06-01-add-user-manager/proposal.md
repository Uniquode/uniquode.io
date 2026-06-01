## Why

Administrative user management is now needed because `identity-foundation`
creates local users and browser-session authentication, but intentionally keeps
public registration closed. Operators need a basic non-UI tool to create,
inspect, update, and remove users while richer administrative UI details remain
separate.

Linear: `UT-179`.

## What Changes

- Add a reusable `auth_ext`-owned CLI script named `usermgr` for administrative
  local-user management.
- Support creating local users, including explicit admin and superuser options.
- Support deleting users through a deliberate, safe command path.
- Support deactivating users without deleting their account row.
- Support updating user attributes such as verification status, admin status,
  superuser status, password, full name, and preferred timezone.
- Support listing users with useful filters and ordering, including
  admins, superusers, email or partial email, creation date, and last-login
  date when that field is available.
- Support interactive password entry with confirmation, plus explicit stdin
  password input for operator automation.
- Add an injectable `auth_ext` password policy boundary that provides strength
  feedback and Result-based validation for local-user password writes.
- Add operational user metadata needed by the CLI: created, modified, last-login,
  expiry, email-verification-sent, display-name, preferred-name, and
  preferred-timezone fields.
- Support readable default output plus JSON and CSV output for scripted use.
- Use `dateparser` for flexible timestamp filter input, with numeric Unix
  timestamps handled directly before parser fallback.
- Decide and implement the initial execution model for the CLI: direct
  auth-package service/FastAPI Users access using generic `[auth]`
  configuration from `auth.toml`, with an API-backed mode deferred until API
  tokens/scopes exist.
- Keep browser/admin UI design out of scope for this change.

## Capabilities

### New Capabilities

- `user-management-cli`: The `usermgr` operational CLI, including user create,
  update, delete, deactivate, list, password-change, filtering, ordering,
  confirmation, output-format, and operator-safety behaviours.

### Modified Capabilities

- None.

## Impact

- `pyproject.toml` project scripts will add `usermgr`.
- `pyproject.toml` runtime dependencies will add `dateparser` for flexible CLI
  timestamp parsing.
- New CLI module(s) will be added under the reusable `auth_ext` identity
  boundary.
- The CLI will depend on the SQLAlchemy async/FastAPI Users identity services
  established by `identity-foundation`.
- Tests will cover command parsing, user creation, admin/superuser creation,
  updates, deletion, deactivation, listing/filtering, output formats, password
  changes, session revocation, and safety prompts.
- No public browser UI is added by this change.
