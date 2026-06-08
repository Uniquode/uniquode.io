## Context

The project already has OpenSpec-driven implementation, ADRs, validation
commands, tests, and reviewer-facing documentation. As the codebase grows, the
maintenance surface now includes operational review, repository hygiene, test
suite coherence, and documentation/spec alignment.

Without an explicit capability, these checks can become informal and are easy to
skip during feature delivery.

## Goals / Non-Goals

**Goals:**

- Establish canonical maintenance expectations for submission-readiness passes.
- Make test cleanup requirement-driven, with behaviour coverage preserved.
- Keep README and canonical OpenSpec content aligned with implementation.
- Provide a capability future maintenance changes can reference.

**Non-Goals:**

- Implement a specific operational polish pass in this change.
- Define exact test coverage percentages or require coverage tooling.
- Add new runtime dependencies, CI jobs, or application features.
- Replace existing ADR or OpenSpec workflow.

## Decisions

### Add A Dedicated Capability

Maintenance expectations will live in a new `project-maintenance` capability
rather than being folded into application infrastructure.

Rationale: application infrastructure describes what the application provides;
maintenance expectations describe how the project is kept reviewable and
coherent over time. Keeping these separate avoids mixing operational
housekeeping with runtime platform behaviour.

### Keep Requirements Workflow-Oriented

The requirements describe review passes and outcomes rather than prescribing a
specific script or checklist format.

Rationale: the project is still evolving, and exact operational workflows will
change. The useful contract is that workspace setup, server startup,
validation, migration, route inspection, auth management, app/runtime checks,
Wevra/app coordination, repository hygiene, and documentation/spec alignment
are checked against implemented behaviour.

### Preserve Behavioural Coverage During Test Cleanup

Test consolidation is allowed only when failures remain clear and equivalent
behaviour coverage remains.

Rationale: parameterisation can reduce repetition, but cleanup must not hide
important configuration, CLI, migration, validation, route inspection, auth
management, web composition, or application runtime coverage.

## Risks / Trade-offs

- [Risk] The spec can become too broad to verify.
  Mitigation: scenarios are written around concrete review passes and explicit
  workflow categories.
- [Risk] Maintenance requirements can drift from current project vocabulary.
  Mitigation: future polish changes should update this capability when workflow
  categories change.
- [Risk] Test consolidation can obscure failures.
  Mitigation: consolidation is explicitly conditional on keeping failures clear.
