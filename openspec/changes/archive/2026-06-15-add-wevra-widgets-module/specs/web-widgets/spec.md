## ADDED Requirements

### Requirement: Widgets module participates in site composition
The system SHALL provide `wevra.widgets` as an optional Wevra module that
participates in normal site composition for templates, static resources, routes,
and context providers.

#### Scenario: Widgets module is included in module order
- **WHEN** site configuration includes `wevra.widgets` in the configured module list
- **THEN** Wevra composes its published templates, static resources, routes, and context providers according to normal module order

#### Scenario: Widgets use normal override semantics
- **WHEN** `wevra.widgets` and another configured module publish the same logical template or static resource path
- **THEN** the resource from the earliest configured module wins according to existing Wevra resource precedence

#### Scenario: Widgets can supersede web defaults
- **WHEN** `wevra.widgets` is ordered before `wevra.web` resource defaults in the effective template resolution order
- **THEN** widget-aware templates can replace low-level `wevra.web` defaults without a separate override mechanism

### Requirement: Widget features are configuration controlled
The system SHALL allow individual `wevra.widgets` features to be enabled or
disabled through widget module configuration.

#### Scenario: Enabled feature contributes web resources
- **WHEN** a widget feature is enabled in configuration
- **THEN** the feature contributes its declared templates, partials, routes, context providers, and static assets to the widgets module surface

#### Scenario: Disabled feature is not published
- **WHEN** a widget feature is disabled in configuration
- **THEN** Wevra does not publish that feature's routes or context providers
- **AND** widget-aware templates do not render that feature's partial by default

#### Scenario: Unknown feature configuration fails clearly
- **WHEN** widget configuration references a feature that `wevra.widgets` does not provide
- **THEN** startup or validation fails with an explicit configuration error identifying the unknown widget feature

### Requirement: Widget layouts are overridable partial compositions
The system SHALL provide widget-aware layout defaults using overridable
templates and partials rather than hidden page mutation.

#### Scenario: Widget-aware layout includes enabled feature partials
- **WHEN** an enabled widget feature is available to the active layout
- **THEN** the widget-aware layout renders that feature through an overridable partial template

#### Scenario: Application overrides widget layout
- **WHEN** an earlier configured application module provides the same logical layout template as `wevra.widgets`
- **THEN** the application layout is used instead of the widget layout

#### Scenario: Application overrides one widget partial
- **WHEN** an earlier configured application module provides the same logical partial template as an enabled widget feature
- **THEN** the application partial is used while other widget layout behaviour remains available

### Requirement: Widgets use capability-based dependencies
Widget features SHALL consume data from other Wevra modules through public site
capabilities, request context, or explicitly contributed context providers rather
than importing provider internals.

#### Scenario: Feature uses available capability
- **WHEN** an enabled widget feature needs data supplied by another module
- **AND** the required public capability is available from the composed site
- **THEN** the feature uses that capability through the public Site capability API

#### Scenario: Optional dependency is absent
- **WHEN** an enabled widget feature has an optional dependency that is not available
- **THEN** the feature degrades without rendering dependency-specific behaviour

#### Scenario: Required dependency is absent
- **WHEN** an enabled widget feature has a required dependency that is not available
- **THEN** startup or validation fails with an explicit error identifying the missing capability or provider requirement

### Requirement: Theme mode selector is a widget feature
The system SHALL provide the `auto`/`light`/`dark` theme mode selector as the
first `wevra.widgets` feature.

#### Scenario: Theme selector renders when enabled
- **WHEN** `wevra.widgets` is configured with the theme selector feature enabled
- **THEN** widget-aware templates render the theme mode selector through an overridable widget partial

#### Scenario: Theme selector updates mode dynamically
- **WHEN** a user changes theme mode through the selector
- **THEN** the request is handled by a `wevra.widgets` route or equivalent widget-owned handler
- **AND** the selected mode is reflected in subsequent rendered pages

#### Scenario: Theme selector can be disabled
- **WHEN** the theme selector feature is disabled
- **THEN** widget-aware templates do not render the selector by default
- **AND** widget-owned selector routes are not published

#### Scenario: Theme selector keeps semantic token ownership separate
- **WHEN** the theme selector changes between `auto`, `light`, and `dark`
- **THEN** it selects the active theme mode without moving semantic token definitions out of the web foundation or application stylesheet layer
