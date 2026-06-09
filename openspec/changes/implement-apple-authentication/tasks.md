## 1. Apple Scope

- [ ] 1.1 Keep Apple login and linking as a provider-specific implementation
  set in `specs/apple-authentication/spec.md`.
- [ ] 1.2 Define Apple-specific client configuration and callback route
  requirements.
- [ ] 1.3 Define Apple claim mapping and subject extraction requirements.

## 2. Runtime Flow

- [ ] 2.1 Add Apple callback validation, state handling, and token verification
  requirements.
- [ ] 2.2 Add provider linking and resolution behaviour through shared external
  identity contracts defined in UT-173.
- [ ] 2.3 Ensure Apple callbacks can record provider assertions in the
  authentication ceremony.

## 3. Validation

- [ ] 3.1 Run `openspec validate implement-apple-authentication --strict`.
- [ ] 3.2 Link implementation details to shared policy contracts from UT-230.
