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

- Add a `usermgr` project script.
- Provide create, delete, list, and password-change operations.
- Support explicit creation of administrative users.
- Support useful list filters and ordering.
- Use the existing application identity service boundaries directly.
- Keep destructive operations deliberate and visible.
- Keep command output scriptable enough for operators and tests.

**Non-Goals:**

- Build a browser-based user-management UI.
- Introduce an admin API token model before the API/authorisation foundation.
- Add role/group/permission editing before the authorisation foundation exists.
- Implement OAuth account linking or advanced-authentication credential
  management.

## Decisions

### Use direct service access first

The first `usermgr` implementation will operate directly against the configured
database and FastAPI Users/application identity services.

Rationale: the application does not yet have an administrative API token/scope
model. Building an API-backed CLI now would require inventing admin token policy
ahead of the API and authorisation foundations.

Future direction: once API tokens and administrative scopes exist, a later
change can add an API-backed mode that authenticates with an admin token and
uses server endpoints instead of direct database access.

### Keep account creation policy explicit

`usermgr create` is a controlled administrative path and does not imply open
public registration. The command should make administrative creation explicit
through flags such as `--admin`.

### Require interactive password confirmation by default

Password changes should prompt for password entry and confirmation by default,
without echoing values. Non-interactive password input may be added later only
when there is a clear automation requirement and a safe secret-input strategy.

### Treat delete as destructive

`usermgr delete` should require a positive confirmation unless a deliberate
force option is provided. Deletion should identify the target user clearly
before removal.

### Model list sorting around available fields

The initial identity model has creation fields only if implementation adds them.
If last-login is not yet tracked, the CLI should define the option but fail
clearly or omit it until a durable last-login field exists. It should not fake
last-login data.

## Risks / Trade-offs

- [Risk] Direct database access bypasses API-level policy. Mitigation: treat
  `usermgr` as a local/operator tool and keep API-backed remote administration
  deferred until scopes and tokens exist.
- [Risk] CLI operations can become unsafe for production data. Mitigation:
  require explicit database configuration, confirmations for destructive
  commands, and tests around command behaviour.
- [Risk] Listing requirements may outpace stored metadata. Mitigation: implement
  available filters first and make unavailable fields explicit rather than
  silently incorrect.

## Migration Plan

1. Add `usermgr` project script.
2. Add command parser and command dispatch module.
3. Add user create command using identity/FastAPI Users services.
4. Add user delete command with confirmation/force behaviour.
5. Add user list command with email/admin filters and supported ordering.
6. Add password change command with interactive confirmation.
7. Add tests for all command behaviours and failure paths.
8. Update validation or documentation if a command smoke check becomes useful.

## Open Questions

- Should `usermgr create` require an explicit `--password-prompt` default, or
  should prompting be implicit when no password option is supplied?
- Should deletion be soft-delete/deactivation instead of hard-delete once the
  authorisation model exists?
- Should last-login be added to the identity model in this change or deferred
  until login audit requirements are specified?
