# route-inspection Specification

## Purpose
TBD - created by archiving change add-route-tree-utility. Update Purpose after archive.
## Requirements
### Requirement: Installed route tree inspection

The system SHALL provide a route-inspection utility that loads the configured
host application and inspects the entire final installed FastAPI/Starlette route
tree.

#### Scenario: Host application routes are inspected

- **WHEN** a developer runs the route-inspection utility from a configured
  Wybra host project
- **THEN** the utility loads the configured host ASGI application target
- **AND** the utility reports routes, mounts, and traversable sub-application
  routes from the installed application route graph

#### Scenario: Prefixed package command is provided

- **WHEN** Wybra package console scripts are installed
- **THEN** the route-inspection utility is exposed as `wybra-routes`
- **AND** host applications are not required to publish a bare `routes` console
  script to use route inspection

#### Scenario: Wybra origin metadata is included when available

- **WHEN** an installed route was included from a configured Wybra module router
- **THEN** the route-inspection output identifies the configured module name and
  router label when that origin metadata is available

#### Scenario: Non-Wybra routes remain visible

- **WHEN** the installed application includes routes or mounts that do not have
  Wybra module-origin metadata
- **THEN** the route-inspection output still lists those routes with best-effort
  route metadata

#### Scenario: Opaque mounts are represented

- **WHEN** the installed application contains a mounted subtree that cannot be
  recursively inspected
- **THEN** the route-inspection output includes the mount as an opaque route
  tree node

### Requirement: Route tree representations

The system SHALL provide succinct text, expanded graph-like text, Mermaid, and
JSON representations of the installed route tree.

#### Scenario: Succinct route tree output is displayed

- **WHEN** a developer requests the succinct route-tree representation
- **THEN** the output uses one compact line per route or mount
- **AND** each line includes the path, method set or mount kind, route name when
  available, origin metadata when available, and endpoint shape summary

#### Scenario: Expanded graph-like route tree output is displayed

- **WHEN** a developer requests the expanded graph-like route-tree
  representation
- **THEN** the output shows the installed route tree as a visually connected
  path hierarchy
- **AND** route leaves include method sets, route names, endpoint identifiers,
  origin metadata when available, and endpoint shape
- **AND** unknown endpoint shape is omitted from graph labels to keep the tree
  compact
- **AND** repeated module-router origin metadata is represented once at the
  nearest route-tree group and omitted from descendants while the inherited
  origin remains unchanged

#### Scenario: Mermaid route tree output is displayed

- **WHEN** a developer requests the Mermaid route-tree representation
- **THEN** the utility emits Mermaid-compatible diagram text representing route
  tree nodes and edges
- **AND** the diagram text identifies routes, mounts, method sets, route names,
  and origin metadata when available

#### Scenario: JSON route tree output is displayed

- **WHEN** a developer requests the JSON route-tree representation
- **THEN** the utility emits structured route tree nodes, flattened route
  records, warnings, and detected problems for machine consumption

#### Scenario: Output format shortcuts are displayed

- **WHEN** a developer requests a route-tree representation through a direct
  output flag
- **THEN** `--succinct`, `--graph`, `--mermaid`, and `--json` select the
  corresponding output representation
- **AND** conflicting output format selectors fail with a clear usage error

#### Scenario: Large route sets remain deterministic

- **WHEN** the installed route tree contains many routes
- **THEN** every output representation uses deterministic ordering so two
  equivalent route trees produce equivalent output

### Requirement: Machine-readable route inspection output

The system SHALL provide a machine-readable output mode for route inspection.

#### Scenario: JSON output contains route records

- **WHEN** a developer requests machine-readable route-inspection output
- **THEN** the utility emits structured tree nodes and route records containing
  path, methods, route name, route kind, endpoint identifier, origin metadata
  when available, endpoint shape, and warnings

#### Scenario: JSON output contains detected problems

- **WHEN** route inspection detects route-surface problems
- **THEN** the machine-readable output includes structured problem records that
  identify the affected routes and problem kinds

### Requirement: Route smoke checks

The system SHALL provide a route smoke-check mode that fails when the installed
route tree contains route-surface problems.

#### Scenario: Endpoint-name collision is detected

- **WHEN** the installed route tree contains duplicate non-blank route names
- **THEN** the route smoke-check mode reports the collision
- **AND** the command exits with a non-zero status

#### Scenario: Method and path collision is detected

- **WHEN** the installed route tree contains duplicate explicit HTTP method and
  path combinations
- **THEN** the route smoke-check mode reports the collision
- **AND** the command exits with a non-zero status

#### Scenario: Clean route tree passes

- **WHEN** the installed route tree contains no detected route-surface problems
- **THEN** the route smoke-check mode exits successfully

#### Scenario: Quiet route check emits no route tree output

- **WHEN** a developer runs route smoke-check mode with quiet output enabled
- **THEN** the command emits no route-tree representation output
- **AND** the command exits successfully for a clean route tree
- **AND** the command exits with a non-zero status for route-surface problems

### Requirement: Endpoint shape reporting

The system SHALL report endpoint shape from runtime route metadata where that
metadata is available.

#### Scenario: API and HTML surfaces are identified

- **WHEN** an installed route has runtime metadata or path/media-type evidence
  indicating API, page, partial, static, mount, or unknown surface type
- **THEN** route-inspection output reports the inferred surface type

#### Scenario: Form or body input is identified

- **WHEN** an installed FastAPI route declares request body or form input
- **THEN** route-inspection output reports that the endpoint accepts body or
  form input

#### Scenario: Path parameters are identified

- **WHEN** an installed route declares path parameters
- **THEN** route-inspection output reports the path parameter names and known
  parameter metadata

#### Scenario: Explicit template metadata is reported

- **WHEN** an installed route exposes explicit template metadata through a
  Wybra-supported metadata convention
- **THEN** route-inspection output reports the template name or logical template
  identifier

#### Scenario: Missing template metadata is not inferred from source

- **WHEN** an installed route renders a template but does not expose explicit
  template metadata
- **THEN** route-inspection output does not parse handler source code to infer
  the template name
- **AND** the template field is reported as unknown or not declared

### Requirement: Route inspection remains separate from validation

The system SHALL keep route-tree inspection and smoke checking separate from the
existing broad validation command.

#### Scenario: Validation command remains focused

- **WHEN** a developer runs the existing validation command
- **THEN** it continues to perform project-structure validation without
  rendering the route tree as its primary concern

#### Scenario: Route checks are explicitly invoked

- **WHEN** a developer or CI job wants route-tree smoke checking
- **THEN** it invokes the route-inspection utility's check mode explicitly
