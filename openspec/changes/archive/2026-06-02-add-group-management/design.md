## Context

The identity foundation now has canonical local users, browser sessions,
operator user management, and an `auth_provider` contract shell. Later work
still depends on an authorisation model that can answer "which scopes does this
subject have?" without embedding policy in the OAuth provider or API layer.

Current user management stores local user metadata on `auth_ext.models.User` and
exposes local administrative operations through `auth_ext.management` and the
`identitymgr` Click command. Existing `is_admin` and `is_superuser` fields are useful
for bootstrap and local management safety, but they are too coarse to be the
durable authorisation model for API tokens, OAuth scopes, and feature-gated
surfaces.

The missing foundation is a group graph:

```text
group
  -> group
  -> user
```

Groups own scopes. Users gain effective scopes through direct group membership
and through nested group membership. Users do not have direct flags in this
change.

## Goals / Non-Goals

**Goals:**

- Add a reusable `auth_ext` group/scope model that is independent of
  `uniquode` application modules.
- Represent groups with an ID, description, and assigned scopes.
- Support group-to-user and group-to-group membership.
- Resolve effective user scopes through recursive group traversal with cycle
  protection and duplicate elimination.
- Add local `identitymgr` group-management operations for operators before
  API-backed administration exists.
- Keep the model suitable for later API-token and `auth_provider` scope policy.

**Non-Goals:**

- Do not implement runtime OAuth2/OIDC provider endpoints in this change.
- Do not add API-backed group administration or administrative API tokens.
- Do not add direct user flags or per-user scope assignments.
- Do not replace `is_admin` or `is_superuser`; keep them as existing identity and
  bootstrap fields.
- Do not define a product-specific permission catalogue beyond string scopes.
- Do not introduce a new runtime dependency.

## Decisions

### 1. Store groups and memberships in `auth_ext`

Group and scope persistence should live under the reusable `auth_ext` package,
alongside the existing identity models. The first storage adapter remains
SQLAlchemy async, using the existing `auth_ext.models.metadata` and Alembic
discovery path.

Proposed tables:

- `identity_group`
  - `id`: stable group identifier
  - `abbrev`: unique operator-facing short name
  - `description`: operator-facing description
- `identity_scope`
  - `scope`: stable scope string
  - `description`: optional documentation text
- `identity_group_scope`
  - `group_id`
  - `scope`
- `identity_group_user`
  - `group_id`
  - `user_id`
- `identity_group_group`
  - `parent_group_id`
  - `child_group_id`

Rationale: keeping group data in `auth_ext` lets identity, user management, API
tokens, and `auth_provider` share one scope policy boundary without importing
`uniquode` application modules.

Alternative considered: store authorisation data in the host application.
Rejected because `auth_provider` and reusable identity flows need a
host-facing contract that can be supplied by any application using `auth_ext`.

### 2. Add a unique group abbreviation for operator UX

Groups should have both a stable ID and a unique operator-facing abbreviation
or short name. CLI commands should accept `<id-or-abbrev>` wherever an operator
needs to identify a group. The abbreviation should be fixed at creation time and
not editable through normal group update operations.

Rationale: stable IDs are appropriate for persistence and integration, but they
are awkward in daily `identitymgr` usage. A unique abbreviation gives operators a
safe, memorable handle without making the human-facing label the only durable
identifier. Making abbreviations immutable avoids broken operator runbooks and
keeps CLI references stable.

Alternative considered: make the primary group ID a human slug. Rejected because
renaming a group should not require changing every stored relationship or future
external reference. A separate unique abbreviation keeps ergonomic lookup and
stable identity distinct.

### 3. Store scopes as described records and assign them to groups

Scopes should be stored as explicit records with stable scope strings and
optional descriptive text, then assigned to groups through a group-scope join
table. Scope strings are the durable capability vocabulary used by API tokens
and future OAuth2/OIDC access decisions.

Scope strings should not be constrained by a configured prefix or pattern in the
first implementation. Such validation would only add policy without a current
requirement, and it would make future naming conventions harder to evolve.

Rationale: scopes map naturally to OAuth and API access, while a scope table
allows operator-facing descriptions and documentation. The join table keeps
group assignments queryable, validates uniqueness, and avoids parsing
space/comma/newline-separated text fields.

Alternative considered: store scopes as delimited text on the group. Rejected
because scope lookup, uniqueness, validation, and documentation are clearer with
normalised scope records.

### 4. Users have no direct flags or direct scopes

Users gain scopes only through group membership. Existing user booleans remain
for current identity management semantics, but they are not expanded into a
general authorisation flag system.

Rationale: one capability path makes effective access easier to reason about,
audit, and test. It also avoids precedence rules between user-level and
group-level capabilities.

Alternative considered: allow direct user flags for overrides. Rejected for this
slice because override semantics would add ambiguity before the product has a
clear requirement for them.

### 5. Resolve scopes recursively with visited-set cycle protection and caching

Effective-scope resolution should start from the user's direct group memberships
and traverse child groups recursively. The resolver should collect scopes from
every reachable group, track visited group IDs, and return a de-duplicated set.

Cycle handling should be enforced in both write and read paths. Management
services should reject group-to-group assignments that would create a cycle, and
selection lists for assigning nested groups should use the same graph reasoning
to present only groups that are currently unseen/reachable-safe for the target
relationship. The resolver should still be defensive: it must never process the
same group more than once and should collect resulting scopes into a set.

Effective scope results should be cached behind the authorisation service
boundary as a runtime-only, on-demand cache. The cache must be invalidated
whenever group membership, nested group membership, scope definitions, or
group-scope assignments change. It should not be persisted.

Rationale: nested groups are a graph, and operational data can become malformed
through migrations, manual database repair, or future import tools. The runtime
resolver must be safe even when stored data is imperfect. Caching keeps repeated
request-time scope checks cheap while keeping invalidation tied to the small set
of mutations that can change effective scopes. A persisted cache would add
complexity without a current need.

Alternative considered: reject all nested groups and keep only flat membership.
Rejected because the requested model explicitly allows groups to contain other
groups.

### 6. Prevent simple invalid membership at service boundaries

Management services should reject:

- group-to-group self-membership;
- duplicate group scopes;
- duplicate user memberships;
- duplicate group memberships;
- group-to-group membership that would create a cycle;
- deletion of a group while users are assigned to it;
- deletion of a group while it contains other groups;
- deletion of a group while another group contains it.

The same scope may be assigned to multiple groups. Effective-scope resolution
folds duplicates by collecting scopes into a set, so `group1 -> scope1` and
`group2 -> scope1` still produce one effective `scope1`.

Rationale: simple validation catches ordinary operator mistakes, while runtime
safety protects every caller. Group deletion should not cascade to users or
silently rewrite the group graph; operators must remove memberships explicitly
before deleting a group.

Alternative considered: enforce full acyclic graph constraints in the database.
Rejected because portable recursive graph constraints across SQLite and
PostgreSQL would add complexity out of proportion to this foundation slice.

### 7. Extend `identitymgr` with group subcommands and user membership options

`identitymgr` should gain group-management capability under a clear command shape,
for example:

- `identitymgr group create <abbrev> --description ... --scope ...`
- `identitymgr group <id-or-abbrev> update --description ... --scope ... --rm-scope ...`
- `identitymgr group <id-or-abbrev> delete [--force]`
- `identitymgr group <id-or-abbrev> show [--json]`
- `identitymgr group <id-or-abbrev> add-user <user-target>`
- `identitymgr group <id-or-abbrev> remove-user <user-target>`
- `identitymgr group <id-or-abbrev> add-group <child-id-or-abbrev>`
- `identitymgr group <id-or-abbrev> remove-group <child-id-or-abbrev>`
- `identitymgr group list [--json|--csv]`
- `identitymgr scope create <scope> --description ...`
- `identitymgr scope update <scope> --description ...`
- `identitymgr scope delete <scope>`
- `identitymgr scope list [--json|--csv]`
- `identitymgr group effective-scopes <user-target>`

User create/update flows should also support group membership:

- `identitymgr create <email> --group <id-or-abbrev> --group <id-or-abbrev>`
- `identitymgr update <user-target> --add-group <id-or-abbrev>`
- `identitymgr update <user-target> --rm-group <id-or-abbrev>`
- `identitymgr update <user-target> --set-group <id-or-abbrev> --set-group <id-or-abbrev>`

`--group` on create is additive because the user has no existing groups.
`update` should avoid a bare `--group` replacement operation because it is too
easy to confuse with additive create semantics. Replacement should be explicit
from the outset through repeatable `--set-group`, while incremental updates use
`--add-group` and the shorter `--rm-group`.

Rationale: local CLI administration is already the accepted path until API
tokens and administrative scopes exist. Keeping group management in the same
tool preserves operator workflow and avoids inventing an admin API prematurely.

Alternative considered: create a separate `groupmgr` script. Rejected because
groups are part of local identity administration and share configuration,
schema preflight, output modes, and target-resolution conventions with
`identitymgr`.

### 8. Keep auth-provider integration contract-only for this slice

This change should provide a scope policy that future `auth_provider` runtime
work can consume. It should not implement OAuth2 endpoints, grants, clients,
consent, token issuance, introspection, or revocation.

Rationale: the accepted auth-provider architecture already defers endpoint work
until local users and authorisation policy are available. This change supplies
the group/scope policy dependency but leaves runtime provider implementation to
`implement-auth-provider-runtime`.

## Risks / Trade-offs

- [Risk] Nested group graphs can create cycles or unexpectedly broad access. →
  Mitigation: resolver visited-set protection, management validation for common
  mistakes, unseen-only nested group selection lists, clear `identitymgr group show`
  and `effective-scopes` output.
- [Risk] String scopes can drift without documentation. → Mitigation:
  store scopes as records with optional descriptions and make group assignments
  reference those scope records.
- [Risk] Runtime effective-scope caches can become stale. → Mitigation:
  invalidate scope caches on every group, membership, scope, or group-scope
  mutation; rebuild on demand rather than persisting cached results.
- [Risk] CLI command surface may become large. → Mitigation: keep group commands
  under a single `identitymgr group` command tree and preserve JSON/CSV/human output
  conventions.
- [Risk] Operator-facing abbreviations can collide or drift from operator
  documentation. → Mitigation: enforce uniqueness, make abbreviations immutable
  after creation, and resolve group targets through a single ID-or-abbreviation
  boundary.
- [Risk] Deleting groups can silently change access for many users. →
  Mitigation: refuse deletion while the group has user memberships, child
  groups, or parent groups; operators must remove relationships explicitly.
- [Risk] Scope resolution can become expensive for deep graphs. → Mitigation:
  keep queries bounded by visited groups, avoid repeated group loads, and add
  targeted tests for deeper membership graphs before optimising.

## Migration Plan

1. Add SQLAlchemy models and Alembic migration for groups, immutable unique
   abbreviations, described scopes, user membership, and nested group
   membership.
2. Add management service functions for group CRUD, membership changes, and
   cached effective-scope resolution.
3. Add `identitymgr group` commands and user create/update group options that call
   the management service boundary and preserve existing output conventions.
4. Add validation coverage for migration metadata and identity-manager schema
   preflight.
5. Document group concepts, scope resolution, and operator examples.

Rollback is standard Alembic downgrade for the new tables. Since this change
introduces new data, downgrading will remove group/scope assignments and should
be treated as destructive for authorisation state.

## Open Questions

- None at this stage.
