## ADDED Requirements

### Requirement: Wybra shortcut ownership
Optional developer shortcut aliases for package-owned commands SHALL live in
the Wybra project and target `wybra-*` commands.

#### Scenario: Developer installs shortcut aliases
- **WHEN** a developer opts into the shortcut aliases
- **THEN** the aliases are sourced from the Wybra project and call `wybra-*` commands
