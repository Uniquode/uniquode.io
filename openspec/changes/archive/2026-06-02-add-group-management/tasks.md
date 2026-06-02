## 1. Persistence And Schema

- [x] 1.1 Add `auth_ext.models` SQLAlchemy models for `identity_group`, `identity_scope`, `identity_group_scope`, `identity_group_user`, and `identity_group_group`.
- [x] 1.2 Add uniqueness, foreign-key, and lookup indexes for group abbreviations, scope strings, group-scope assignments, user memberships, and nested group memberships.
- [x] 1.3 Add the Alembic migration under `src/uniquode/migrations/versions` for the new authorisation tables and downgrade removal.
- [x] 1.4 Extend the identity-manager identity schema preflight so stale auth databases report missing group/scope tables or columns before command execution.
- [x] 1.5 Add migration metadata tests confirming the new tables are part of the reusable `auth_ext` metadata and application migration discovery.

## 2. Group And Scope Services

- [x] 2.1 Define management result errors and record helpers for groups, scopes, group memberships, and effective-scope output.
- [x] 2.2 Implement group target resolution by stable ID or immutable unique abbreviation.
- [x] 2.3 Implement scope create, update-description, remove-unused, list, and lookup operations without prefix or pattern validation.
- [x] 2.4 Implement group create, update-description, list, show, and delete operations while keeping abbreviations immutable.
- [x] 2.5 Implement group-scope assignment and removal with duplicate assignment rejection while allowing the same scope on multiple groups.
- [x] 2.6 Implement user-group membership assignment and removal with duplicate membership rejection.
- [x] 2.7 Implement group-group membership assignment and removal with duplicate, self-membership, and cycle rejection.
- [x] 2.8 Implement candidate child-group discovery that excludes already seen or cycle-producing groups for the selected parent.
- [x] 2.9 Implement group deletion safety so deletion is rejected while users, child groups, or parent groups reference the group.

## 3. Effective Scope Resolution

- [x] 3.1 Implement recursive effective-scope resolution starting from direct user group memberships and traversing child groups.
- [x] 3.2 Track visited group IDs during resolution so each group is processed at most once even if stored data is malformed.
- [x] 3.3 Collect effective scope strings into a set so duplicate scopes reached through multiple groups are folded.
- [x] 3.4 Return no direct scopes for users with no group membership.
- [x] 3.5 Add a runtime-only, on-demand effective-scope cache behind the authorisation service boundary.
- [x] 3.6 Invalidate cached effective scopes after group, scope, group-scope, user-group, or group-group mutations.
- [x] 3.7 Expose group-backed capability resolution through the identity boundary without treating `is_admin` or `is_superuser` as general authorisation scopes.

## 4. User Manager CLI

- [x] 4.1 Add `identitymgr scope create`, `identitymgr scope update`, `identitymgr scope delete`, and `identitymgr scope list` commands using existing configuration, database, and output-mode conventions.
- [x] 4.2 Add `identitymgr group create`, `identitymgr group list`, `identitymgr group <id-or-abbrev> update`, `identitymgr group <id-or-abbrev> show`, and `identitymgr group <id-or-abbrev> delete` commands.
- [x] 4.3 Add `identitymgr group <id-or-abbrev> add-user` and `identitymgr group <id-or-abbrev> remove-user` commands for direct user membership.
- [x] 4.4 Add `identitymgr group <id-or-abbrev> add-group` and `identitymgr group <id-or-abbrev> remove-group` commands for nested group membership.
- [x] 4.5 Add repeatable `--scope` and `--rm-scope` options to `identitymgr group <id-or-abbrev> update` for assigning and removing group scope assignments.
- [x] 4.6 Add `identitymgr group effective-scopes <user-target>` with human and JSON output that includes user, group path, and de-duplicated scope data without password material.
- [x] 4.7 Add repeatable `--group <id-or-abbrev>` support to `identitymgr create` and assign the new user to the requested groups in the same management flow.
- [x] 4.8 Add repeatable `--add-group`, `--rm-group`, and `--set-group` support to `identitymgr update` with explicit replacement only through `--set-group`.
- [x] 4.9 Reject `identitymgr update --group` with a usage error that directs operators to `--set-group`, `--add-group`, or `--rm-group`.

## 5. Auth Provider Contract Alignment

- [x] 5.1 Update host-facing auth-provider scope policy contracts or adapters so allowed scopes can be supplied from group-backed effective-scope resolution.
- [x] 5.2 Preserve the provider boundary as contract-only for this change, with no OAuth2/OIDC endpoint, grant, client, token issuance, consent, introspection, or revocation runtime implementation.
- [x] 5.3 Add tests or contract examples showing duplicate reachable scopes are represented once before the provider consumes them.

## 6. Tests And Documentation

- [x] 6.1 Add service tests for group creation, immutable abbreviation handling, duplicate group abbreviation rejection, group description updates, listing, showing, and deletion safety.
- [x] 6.2 Add service tests for scope creation, description updates, unused-scope removal, used-scope removal rejection, duplicate scope rejection, and unconstrained scope strings.
- [x] 6.3 Add service tests for group-scope, user-group, and group-group duplicate rejection.
- [x] 6.4 Add service tests for self-membership rejection, deeper cycle rejection at write time, and defensive cycle-safe read-time resolution.
- [x] 6.5 Add service tests for effective-scope resolution across direct groups, nested groups, duplicated scopes, missing membership, and runtime cache invalidation.
- [x] 6.6 Add CLI tests for the group and scope command trees, target resolution by ID or abbreviation, JSON/CSV/human output, and operator error messages.
- [x] 6.7 Add CLI tests for create `--group`, update `--add-group`, update `--rm-group`, update `--set-group`, and rejected update `--group` behaviour.
- [x] 6.8 Update operator documentation with group, scope, membership, and effective-scope examples.
- [x] 6.9 Run `openspec validate add-group-management --strict` and the relevant project test commands for the changed auth extension and identity-manager surfaces.
