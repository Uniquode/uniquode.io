# 0006: Authorisation and Access-Control Model

Date: 2026-05-20

Status: Provisional

## Context

The project requires access control beyond simple authentication.

The application must support:

- public pages that require no login;
- authenticated pages and actions;
- administrative surfaces;
- access rules based on group membership;
- access rules based on specific flags or capabilities;
- access rules based on OAuth2 or API scopes where relevant;
- internal organisations as administrative user assignments, without treating organisations as tenants.

The project is explicitly single-tenant. Organisations exist for internal grouping and assignment, not for tenant isolation or per-tenant routing.

Groups are intended primarily as permission and capability models, and may also carry user-defined flags that gate access to functionality.

The access-control model must work consistently across HTML pages, dynamic partial endpoints, APIs, and administrative workflows.

Identity-foundation planning separated authentication, advanced authentication, and delegated authorisation into distinct boundaries. The future internal `auth-provider` package will depend on this authorisation model for group, flag, and scope policy while remaining independent of FastAPI Users and `fastapi-users-auth-ext`.

## Decision

Use a layered authorisation model with distinct concepts for authentication state, groups, flags, scopes, and organisation assignment.

Treat groups as the primary permission and capability containers.

Allow groups to carry user-defined flags that can be used as additional access gates where simple group membership is too coarse.

Allow access rules to depend on OAuth2 scopes or API scopes where the relevant endpoint or integration uses scope-based authorisation.

Define scope policy so it can be consumed by the later internal `auth-provider` package through explicit interfaces rather than by embedding group or flag logic in the OAuth2 provider itself.

Support internal organisation assignment for users, with users able to belong to one or more organisations.

Do not treat organisations as tenants, isolation boundaries, or routing partitions.

Allow administrative users to change group membership, organisation assignment, and related access metadata at any time, subject to administrative policy.

Attach access policy explicitly to routes, pages, partial endpoints, and APIs through code-defined metadata or policy bindings rather than by embedding policy decisions in templates or in database-defined route definitions.

Support public routes explicitly rather than inferring public access from missing policy.

## Consequences

The project gets a consistent way to express access requirements across browser pages and machine-facing APIs.

Separating groups, flags, scopes, and organisations avoids overloading one concept to solve unrelated problems.

Keeping organisations non-tenant avoids premature complexity in routing, data isolation, and provisioning.

Administrative reassignment of users, groups, and organisations supports operational flexibility but means access changes must propagate cleanly to session checks, token checks, and cached policy views.

Explicit policy attachment should make routes easier to audit and export, but it requires a clear naming and metadata convention.

Keeping scope policy outside `auth-provider` lets the OAuth2 provider remain an Authlib integration layer while the application authorisation model owns the meaning of groups, flags, and scopes. The trade-off is that the authorisation foundation must provide clear interfaces for allowed-scope calculation and policy audit.

## Open Questions

- Whether user-defined flags should exist only on groups or also directly on users.
- Whether scopes should be a separate first-class model from flags or initially mapped through one policy layer.
- How much of the access-control policy should be exportable in the route manifest.
- Whether organisation membership should ever participate directly in authorisation rules or remain purely informational and administrative.
- How the later `auth-provider` boundary should request allowed scopes for a subject and client.

## Follow-Up Work

- Define the group, organisation, flag, and scope models.
- Define route and endpoint policy metadata conventions.
- Define administrative management flows for assignments and access changes.
- Define how policy checks apply to sessions, API tokens, and OAuth2-scoped requests.
- Define the scope-policy interface that the later internal `auth-provider` package will consume.

## Revision Notes

- 2026-05-24: Added the relationship between group, flag, and scope policy and the future internal `auth-provider` Authlib integration boundary.
