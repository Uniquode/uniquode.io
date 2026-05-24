## Why

Administrative user management is now needed because `identity-foundation`
creates local users and browser-session authentication, but intentionally keeps
public registration closed. Operators need a basic non-UI tool to create,
inspect, update, and remove users while richer administrative UI details remain
separate.

Linear: `UT-179`.

## What Changes

- Add a project CLI script named `usermgr` for administrative local-user
  management.
- Support creating local users, including an explicit administrative-user
  option.
- Support deleting users through a deliberate, safe command path.
- Support listing users with useful filters and ordering, including
  administrative users, email or partial email, creation date, and last-login
  date when that field is available.
- Support interactive password change with confirmation.
- Decide and implement the initial execution model for the CLI:
  application-local service/FastAPI Users access first, with an API-backed mode
  deferred until API tokens/scopes exist.
- Keep browser/admin UI design out of scope for this change.

## Capabilities

### New Capabilities

- `user-management-cli`: The `usermgr` operational CLI, including user create,
  delete, list, password-change, filtering, ordering, confirmation, and
  operator-safety behaviours.

### Modified Capabilities

- None.

## Impact

- `pyproject.toml` project scripts will add `usermgr`.
- New CLI module(s) will be added under the application identity boundary.
- The CLI will depend on the SQLAlchemy async/FastAPI Users identity services
  established by `identity-foundation`.
- Tests will cover command parsing, user creation, admin creation, deletion,
  listing/filtering, password changes, and safety prompts.
- No public browser UI is added by this change.
