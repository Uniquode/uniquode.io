## Why

Linear: [UT-213](https://linear.app/uniquode/issue/UT-213/add-group-management)
Parent: [UT-172](https://linear.app/uniquode/issue/UT-172/authorisation-foundation)

The identity foundation and user management work introduced local users,
administrative user flags, and a local operator CLI, but the application still
lacks the authorisation component that later API tokens, scopes, and OAuth2
provider work depend on. The missing foundation is group-managed scope
resolution: groups own scopes, groups can contain users and other groups, and
effective user capabilities are resolved by recursively traversing that graph.

## What Changes

- Introduce groups as authorisation capability containers.
- Model each group with an `id`, `description`, and one or more scopes.
- Allow a group to contain both users and other groups.
- Resolve effective capabilities by recursively searching group membership and
  nested group membership so every reachable scope is included.
- Handle duplicate memberships and group cycles without double-counting scopes
  or recursing indefinitely.
- Record the decision that users require no direct flags; groups and scopes are
  the durable capability mechanism.
- Add group-management operations to `identitymgr` so local operators can manage
  groups before API-backed administration exists.
- Preserve existing `is_admin` and `is_superuser` user fields as local identity
  and bootstrap/user-management state rather than treating them as the long-term
  authorisation model.

## Capabilities

### New Capabilities

- `authorisation-groups`: Group records, group-to-group membership,
  group-to-user membership, scope assignment, and recursive effective-scope
  resolution.

### Modified Capabilities

- `user-management-cli`: Add local group-management commands for creating,
  updating, listing, inspecting, assigning, unassigning, and deleting groups.
- `identity-authentication`: Resolve local user capabilities through group
  membership where route, page, partial, API, or token policy needs scopes.
- `auth-provider`: Use host-provided scope policy backed by groups when runtime
  OAuth2/OIDC provider work begins.

## Impact

- Affected areas include `auth_ext` authorisation contracts, persistence models,
  Alembic migrations, `identitymgr`, validation, tests, and operator documentation.
- This change is a prerequisite for API tokens/scopes and for completing
  API-backed user-management behaviour.
- Auth-provider runtime implementation remains deferred, but it should consume
  the group/scope policy defined here instead of embedding its own scope model.
