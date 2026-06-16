## ADDED Requirements

### Requirement: Wybra command names
Package-owned command line entry points SHALL use `wybra-*` command names.

#### Scenario: Developer invokes package command
- **WHEN** a developer runs a package-owned command
- **THEN** the command name uses the `wybra-*` prefix
