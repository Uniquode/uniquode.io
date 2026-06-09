## 1. Data Model and Migration

- [ ] 1.1 Add a new SQLAlchemy model `identity_user_email` in `wevra.auth` with fields for `id` (or `(user_id, email)`), `user_id`, `email`, `is_primary`, and `is_verified`.
- [ ] 1.2 Add uniqueness and indexing constraints for `identity_user_email` to enforce one local user per normalized email and fast lookups.
- [ ] 1.3 Add Alembic migration(s) for new table and indexes that match the model metadata and normalisation expectations.

## 2. Authentication Resolution Refactor

- [ ] 2.1 Introduce an email-principal lookup path that resolves local users via `identity_user_email`.
- [ ] 2.2 Update password login flow to accept any owned email address and remove single-email assumptions from lookup logic.
- [ ] 2.3 Update password + TOTP ceremony start to share the same email principal resolution path.
- [ ] 2.4 Update FastAPI Users strategy integration boundaries to consume the new principal resolver.

## 3. Provider and Passkey Integration

- [ ] 3.1 Update provider callback/link flows to map claimed emails through `identity_user_email`.
- [ ] 3.2 Ensure passkey assertion completion applies to the same resolved user context used by password/email lookup.
- [ ] 3.3 Preserve conflict handling for callback collisions and maintain deterministic non-reassignment behaviour.

## 4. Validation and Test Coverage

- [ ] 4.1 Add tests in `wevra` for model uniqueness and lookup by any owned email.
- [ ] 4.2 Add tests in `app` for login flows using secondary email addresses and no cross-account email ownership.
- [ ] 4.3 Add/adjust tests for provider callback and passkey paths with shared principal resolution.
- [ ] 4.4 Run focused authentication and environment settings test suites, then full affected module checks.
