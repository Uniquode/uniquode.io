## 1. Command Contract

- [ ] 1.1 Add `usermgr` to project scripts.
- [ ] 1.2 Add command parser and dispatch for `create`, `delete`, `list`, and `password` or equivalent password-change command.
- [ ] 1.3 Keep command implementation async-compatible with the identity persistence boundary.

## 2. User Operations

- [ ] 2.1 Implement user creation through the existing identity/FastAPI Users services.
- [ ] 2.2 Add an explicit administrative-user option for create.
- [ ] 2.3 Implement duplicate-user handling with a clear non-zero failure.
- [ ] 2.4 Implement user deletion with confirmation and a deliberate force option.
- [ ] 2.5 Implement user listing with email and admin filters.
- [ ] 2.6 Implement supported list ordering, including clear handling for last-login if that field is not yet available.
- [ ] 2.7 Implement interactive password change with hidden password entry and confirmation.

## 3. Safety And Documentation

- [ ] 3.1 Document that the initial CLI uses local service/database access rather than an admin API token.
- [ ] 3.2 Document that API-backed operation is deferred until administrative API tokens/scopes exist.
- [ ] 3.3 Ensure destructive operations identify the target user clearly before proceeding.

## 4. Validation

- [ ] 4.1 Add focused tests for command parser and dispatch.
- [ ] 4.2 Add focused tests for create, create-admin, duplicate create, delete, list filters, and password change.
- [ ] 4.3 Add tests for confirmation and mismatch failure paths.
- [ ] 4.4 Run `uv run ruff format --check`, `uv run ruff check`, `uv run ty check src/`, `gtimeout 30s uv run pytest`, and `uv run openspec validate add-user-manager --strict`.
