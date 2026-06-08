## Why

Linear: [UT-227](https://linear.app/uniquode/issue/UT-227/add-project-maintenance-spec)

The project needs an explicit maintenance contract for keeping submissions
reviewable, tests coherent, and documentation/specifications aligned as the
implementation grows.

This prevents operational review, test cleanup, and documentation hygiene from
being treated as optional or ad hoc work after feature implementation.

## What Changes

- Add a new `project-maintenance` capability covering submission-readiness
  review, repository hygiene, test-suite maintenance, and documentation/spec
  hygiene.
- Define reviewer-facing operational workflows that must be checked before
  submission.
- Define expectations for consolidating tests without losing behaviour
  coverage.
- Define expectations for keeping README and canonical OpenSpec content aligned
  with implementation.

## Capabilities

### New Capabilities

- `project-maintenance`: Ongoing project reviewability, repository hygiene,
  test-suite maintenance, and documentation/spec alignment.

### Modified Capabilities

- None.

## Impact

- Adds OpenSpec requirements only.
- Does not add runtime dependencies, APIs, data models, or application
  behaviour.
- Future maintenance/polish changes can reference this capability when checking
  repository hygiene, test inventory, README accuracy, and stale spec wording.
