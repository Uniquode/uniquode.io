## Context

The current authentication model stores a single email directly on `identity_user` and
uses that row as the only login selector for password and provider callbacks.
This is too restrictive for the next phase: users need to own multiple email
addresses without duplicating user records.

There are no active deployed users and no published runtime contracts that
depend on historical email semantics, so we can treat this as a direct schema
refactor without compatibility migrations or compatibility shims.

## Goals / Non-Goals

**Goals:**

- Introduce a normalised `identity_user_email` relation that can hold multiple
  addresses per local user.
- Enforce uniqueness so one email belongs to at most one user globally.
- Resolve authentication principals (password and MFA challenge starts) from any
  owned email.
- Preserve local user as the canonical identity across fast-path and ceremony flows.
- Keep provider callback login/linking and passkey login compatible with the same principal
  resolution path.

**Non-Goals:**

- No support for legacy username-based or non-email login identifiers in this change.
- No provider-specific business policy changes beyond using the canonical email relation for
  user resolution.
- No retention of old multi-row email semantics in alternate fields or duplicate
  lookup paths.

## Decisions

### Decision 1: model email ownership as a dedicated table

Create `identity_user_email(user_id, email, is_primary, is_verified)` with
`UNIQUE(email)`, explicit FK to `identity_user`, and stable indexes for lookup and
uniqueness checks.

**Why:** this cleanly represents the proposition "users may have multiple
emails" and enables deterministic collisions checks.

### Decision 2: enforce canonical email normalisation

Persisted lookup keys should use lowercase/normalised email values and a non-null
`email` column. Canonicalisation prevents accidental duplicates by case and
trailing whitespace variance.

**Why:** prevents bypasses and duplicate logical addresses in constraints.

### Decision 3: resolve login principal by email relation first

All email-based principal lookups should resolve `user_id` through
`identity_user_email` before invoking password/TOTP/passkey/ceremony code.

**Why:** keeps one canonical user subject while allowing all supported login
methods to share the same identity resolution path.

### Decision 4: keep provider matching deterministic

Provider linking/callbacks that currently receive email claims should map to local
users through the email relation first, and only then apply provider-specific linking rules.

**Why:** avoids duplicate matching paths and ensures an email can never map to two
different users.

## Risks / Trade-offs

- [Risk] Additional join for login/email lookup could impact hot-path latency.
  → Mitigation: add indexes on `identity_user_email(user_id)` and
  `identity_user_email(email)` and keep `identity_user.email` as optional fast-path
  mirror only if needed.
- [Risk] Existing auth tests may implicitly assert a single email on user rows.
  → Mitigation: update tests to assert behaviour at the relation level and add
  dedicated uniqueness/lookup coverage.
- [Risk] Provider callback workflows may currently assume one row per local email.
  → Mitigation: explicitly sequence provider email resolution through the new
  relation and enforce one-to-one email ownership.

## Migration Plan

1. Add `identity_user_email` table and migration constraints in `wevra.auth`.
2. Migrate internal lookup/query helpers to resolve users by `identity_user_email`.
3. Update login ceremony entry points so password and TOTP follow the same lookup
   contract; ensure passkey/provider callbacks also consume the new resolution.
4. Update tests and fixtures for the new relation, including uniqueness and multiple
   email login coverage.

## Open Questions

- None.
