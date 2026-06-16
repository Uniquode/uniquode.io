# project-maintenance Specification

## Purpose
TBD - created by archiving change add-project-maintenance-spec. Update Purpose after archive.
## Requirements
### Requirement: Submission Readiness Review
The project SHALL perform a final operational review before submission.

#### Scenario: Reviewer workflow is checked
- **WHEN** a submission-readiness pass begins
- **THEN** the documented workspace setup, development server, validation,
  migration, route inspection, auth management, application test, Wybra test,
  and cross-repository Wybra/app coordination workflows are checked against the
  implemented project

#### Scenario: Repository hygiene is checked
- **WHEN** a submission-readiness pass reviews repository contents
- **THEN** local-only artefacts such as databases, media uploads, logs, caches,
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
- **THEN** they are consolidated with parameterisation when that keeps failures
  clear

#### Scenario: Coverage is preserved
- **WHEN** tests or fixtures are removed, updated, or consolidated
- **THEN** equivalent behavioural coverage remains for configuration loading,
  CLI wrappers, migration lifecycle, validation, web composition, route
  inspection, auth management, and application runtime workflows

### Requirement: Documentation And Spec Hygiene
The project SHALL keep reviewer-facing documentation and canonical specs aligned
with implemented behaviour.

#### Scenario: README is reviewed
- **WHEN** an operational polish pass reviews documentation
- **THEN** the README describes current architecture, assumptions, trade-offs,
  workspace setup, runtime configuration, development server commands,
  validation, migration, auth management, route inspection, cross-repository
  Wybra/app workflow, and test commands

#### Scenario: Specs are reviewed
- **WHEN** an operational polish pass reviews OpenSpec artefacts
- **THEN** canonical specifications are checked for stale, duplicated, or
  overlapping requirements

#### Scenario: Stale wording is corrected
- **WHEN** documentation or canonical specs no longer match implemented
  behaviour
- **THEN** they are updated through the maintenance change to match the
  implemented project
