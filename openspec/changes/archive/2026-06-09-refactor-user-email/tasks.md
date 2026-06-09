## 1. Data Model and Migration

- [x] 1.1 Add a new SQLAlchemy model `identity_user_email` in `wevra.auth` with fields for `id` (or `(user_id, email)`), `user_id`, `email`, `is_primary`, and `is_verified`.
- [x] 1.2 Add uniqueness and indexing constraints for `identity_user_email` to enforce one local user per normalized email and fast lookups.
- [x] 1.3 Add Alembic migration(s) for new table and indexes that match the model metadata and normalisation expectations.

## 2. Authentication Resolution Refactor

- [x] 2.1 Introduce an email-principal lookup path that resolves local users via `identity_user_email`.
- [x] 2.2 Update password login flow to accept any owned email address and remove single-email assumptions from lookup logic.

## 3. Validation and Test Coverage

- [x] 3.1 Add tests in `wevra` for model uniqueness and lookup by any owned email.
- [x] 3.2 Run focused authentication and environment settings test suites, then full affected module checks.
