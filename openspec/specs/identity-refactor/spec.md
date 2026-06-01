# identity-refactor Specification

## Purpose
Define the structural refactor that moved identity implementation code into the
top-level `auth_ext` package while preserving host application behaviour.

## Requirements

### Requirement: Independent `auth_ext` package boundary
The system SHALL promote identity implementation code into the independent
top-level `auth_ext` package rather than keeping it under `uniquode.identity`.

#### Scenario: `auth_ext` package is top-level
- **WHEN** a developer inspects the source tree
- **THEN** identity-domain code lives under the top-level `auth_ext` package rather
  than under the `uniquode` application package

#### Scenario: `auth_ext` package does not import host application code
- **WHEN** the `auth_ext` package is inspected
- **THEN** it does not import `uniquode`, `uniquode.settings`,
  `uniquode.persistence`, application templates, or application route modules

#### Scenario: Dependency direction is one-way
- **WHEN** the host application integrates identity
- **THEN** `uniquode` depends on `auth_ext` and `auth_ext`
  does not depend back on `uniquode`

### Requirement: Host application integration layer
The system SHALL keep `uniquode` as the web interface and host integration layer
for `auth_ext` capabilities.

#### Scenario: Host adapts settings
- **WHEN** identity options are needed
- **THEN** `uniquode` adapts its application settings into `auth_ext`
  options/config objects before passing them to the package

#### Scenario: Host composes presentation
- **WHEN** identity pages or fragments are rendered
- **THEN** `uniquode` owns the templates, route composition, redirects, and
  user-facing copy

#### Scenario: Host selects persistence
- **WHEN** identity persistence is configured
- **THEN** `uniquode` selects and configures a concrete identity persistence
  adapter rather than `auth_ext` importing application persistence
  modules

### Requirement: Behaviour-preserving structural refactor
The `identity-refactor` sub-spec SHALL preserve existing identity behaviour while
changing package structure.

#### Scenario: No new identity behaviour is introduced
- **WHEN** the `identity-refactor` sub-spec is implemented
- **THEN** it does not add new account lifecycle, authentication, or advanced
  authentication behaviour beyond preserving existing behaviour through the new
  package boundary

#### Scenario: Existing tests are repaired
- **WHEN** tests reference identity code
- **THEN** they are updated to import through the new `auth_ext` package boundary
  and continue to validate the same behaviours

#### Scenario: Boundary is validated
- **WHEN** validation or tests run
- **THEN** they include a check that `auth_ext` remains independent of
  `uniquode`
