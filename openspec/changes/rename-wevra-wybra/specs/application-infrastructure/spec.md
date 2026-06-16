## ADDED Requirements

### Requirement: Wybra project identity
The project infrastructure SHALL identify the package and repository as Wybra
using `wybra` package, source, repository, and workspace names.

#### Scenario: Project metadata uses Wybra
- **WHEN** project metadata, workspace dependency declarations, source mappings, or repository links are inspected
- **THEN** they refer to `wybra` or Wybra rather than `wevra` or Wevra
