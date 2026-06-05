## ADDED Requirements

### Requirement: Wevra framework namespace
The system SHALL move reusable framework infrastructure into an explicit
`wevra` package namespace while keeping `uniquode` as the concrete host
application package.

#### Scenario: Reusable infrastructure uses the framework namespace
- **WHEN** the reusable web, data, settings, tooling, and auth infrastructure is
  inspected after the namespace refactor
- **THEN** those reusable packages are imported through `wevra.*` package paths
  rather than temporary top-level infrastructure package names or the
  `uniquode` application package

#### Scenario: Host application remains separate
- **WHEN** a developer inspects the `uniquode` package after the namespace
  refactor
- **THEN** it contains application policy, settings adapters, startup wiring,
  health routes, and application-specific validation rather than reusable
  framework infrastructure

#### Scenario: Behaviour is preserved through the namespace refactor
- **WHEN** the namespace refactor is applied
- **THEN** runtime startup, route composition, template rendering, static asset
  serving, validation, migration commands, and migration graph behaviour remain
  equivalent apart from documented import path, package data, and configured
  module name changes

#### Scenario: Compatibility shims are explicit
- **WHEN** the namespace refactor design is completed
- **THEN** any temporary compatibility shim is justified by a concrete consumer
  requirement rather than being introduced by default
