## MODIFIED Requirements

### Requirement: Theme-aware styling is semantic across templates
The system SHALL apply theme-aware styling through semantic design roles and
tokens across the HTML foundation rather than through template-local light or
dark colour assumptions. The HTML foundation SHALL own semantic theme behaviour
and token expectations, while optional theme-selection UI belongs to composed UI
support modules such as `wevra.widgets`.

#### Scenario: Base templates consume semantic styling roles
- **WHEN** a developer inspects the base page templates and shared components
- **THEN** they rely on semantic styling roles such as background, surface, text, muted text, border, and accent rather than hard-coded mode-specific colour choices in template markup

#### Scenario: Theme mode changes token values rather than template structure
- **WHEN** the active theme mode changes between `auto`, `light`, and `dark`
- **THEN** the visual change is achieved by changing semantic token values and inherited styling rather than by branching the template structure per mode

#### Scenario: Project CSS defines mode-aware semantic tokens
- **WHEN** a developer inspects the project-specific stylesheet layer
- **THEN** the stylesheet defines semantic theme tokens or equivalent variables that support `auto`, `light`, and `dark` behaviour for the shared HTML foundation

#### Scenario: Theme selector UI is not owned by the web foundation
- **WHEN** a developer inspects the low-level web foundation templates and routes
- **THEN** the optional `auto`/`light`/`dark` selector UI is not implemented as a core `wevra.web` concern
- **AND** selector UI behaviour is provided by a composed UI support module when enabled
