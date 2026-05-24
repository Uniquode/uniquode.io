## ADDED Requirements

### Requirement: Submission Readiness Review
The project SHALL perform a final operational review before submission.

#### Scenario: Reviewer workflow is checked
- **WHEN** a submission-readiness pass begins
- **THEN** the documented setup, server, admin, CLI import, upload API,
  background import, reading search, and test workflows are checked against the
  implemented project

#### Scenario: Repository hygiene is checked
- **WHEN** a submission-readiness pass reviews repository contents
- **THEN** local-only artifacts such as databases, media uploads, logs, caches,
  virtual environments, and generated archives are excluded from version control

### Requirement: Test Suite Maintenance
The project SHALL keep tests and fixtures coherent as behaviour evolves.

#### Scenario: Test inventory is inspected
- **WHEN** an operational polish pass reviews the test suite
- **THEN** current test modules and sample fixtures are inventoried before
  cleanup changes are made

#### Scenario: Redundant tests are consolidated
- **WHEN** repeated tests use the same setup and assertion shape with different
  cases
- **THEN** they are consolidated with parameterization when that keeps failures
  clear

#### Scenario: Coverage is preserved
- **WHEN** tests or fixtures are removed, updated, or consolidated
- **THEN** equivalent behavioural coverage remains for parser, CLI, import, API,
  search, admin, and background import workflows

### Requirement: Documentation And Spec Hygiene
The project SHALL keep reviewer-facing documentation and canonical specs aligned
with implemented behaviour.

#### Scenario: README is reviewed
- **WHEN** an operational polish pass reviews documentation
- **THEN** the README describes current architecture, assumptions, trade-offs,
  setup commands, import workflows, search workflows, admin access, and test
  commands

#### Scenario: Specs are reviewed
- **WHEN** an operational polish pass reviews OpenSpec artifacts
- **THEN** canonical specifications are checked for stale, duplicated, or
  overlapping requirements

#### Scenario: Stale wording is corrected
- **WHEN** documentation or canonical specs no longer match implemented
  behaviour
- **THEN** they are updated through the maintenance change to match the
  implemented project
