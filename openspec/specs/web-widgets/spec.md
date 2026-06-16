# web-widgets Specification

## Purpose
Define reusable, module-composed UI widget support for Wybra sites, including
widget feature configuration, widget-aware layouts, overridable partials,
dynamic widget routes, and widget context providers.
## Requirements
### Requirement: Widgets module participates in site composition
The system SHALL provide `wybra.widgets` as an optional Wybra module that
participates in normal site composition for templates, static resources, routes,
and context providers.

#### Scenario: Widgets module is included in module order
- **WHEN** site configuration includes `wybra.widgets` in the configured module list
- **THEN** Wybra composes its published templates, static resources, routes, and context providers according to normal module order

#### Scenario: Widgets use normal override semantics
- **WHEN** `wybra.widgets` and another configured module publish the same logical template or static resource path
- **THEN** the resource from the earliest configured module wins according to existing Wybra resource precedence

#### Scenario: Widgets can supersede web defaults
- **WHEN** `wybra.widgets` is ordered before `wybra.web` resource defaults in the effective template resolution order
- **THEN** widget-aware templates can replace low-level `wybra.web` defaults without a separate override mechanism

### Requirement: Widget features are configuration controlled
The system SHALL allow individual `wybra.widgets` features to be enabled or
disabled through widget module configuration.

#### Scenario: Enabled feature contributes web resources
- **WHEN** a widget feature is enabled in configuration
- **THEN** the feature contributes its declared templates, partials, routes, context providers, and static assets to the widgets module surface

#### Scenario: Disabled feature is not published
- **WHEN** a widget feature is disabled in configuration
- **THEN** Wybra does not publish that feature's routes or context providers
- **AND** widget-aware templates do not render that feature's partial by default

#### Scenario: Unknown feature configuration fails clearly
- **WHEN** widget configuration references a feature that `wybra.widgets` does not provide
- **THEN** startup or validation fails with an explicit configuration error identifying the unknown widget feature

### Requirement: Widget layouts are overridable partial compositions
The system SHALL provide widget-aware layout defaults using overridable
templates and partials rather than hidden page mutation.

#### Scenario: Widget-aware layout includes enabled feature partials
- **WHEN** an enabled widget feature is available to the active layout
- **THEN** the widget-aware layout renders that feature through an overridable partial template

#### Scenario: Application overrides widget layout
- **WHEN** an earlier configured application module provides the same logical layout template as `wybra.widgets`
- **THEN** the application layout is used instead of the widget layout

#### Scenario: Application overrides one widget partial
- **WHEN** an earlier configured application module provides the same logical partial template as an enabled widget feature
- **THEN** the application partial is used while other widget layout behaviour remains available

### Requirement: Widgets use capability-based dependencies
Widget features SHALL consume data from other Wybra modules through public site
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
first `wybra.widgets` feature.

#### Scenario: Theme selector renders when enabled
- **WHEN** `wybra.widgets` is configured with the theme selector feature enabled
- **THEN** widget-aware templates render the theme mode selector through an overridable widget partial

#### Scenario: Theme selector updates mode dynamically
- **WHEN** a user changes theme mode through the selector
- **THEN** the request is handled by a `wybra.widgets` route or equivalent widget-owned handler
- **AND** the selected mode is reflected in subsequent rendered pages

#### Scenario: Theme selector can be disabled
- **WHEN** the theme selector feature is disabled
- **THEN** widget-aware templates do not render the selector by default
- **AND** widget-owned selector routes are not published

#### Scenario: Theme selector keeps semantic token ownership separate
- **WHEN** the theme selector changes between `auto`, `light`, and `dark`
- **THEN** it selects the active theme mode without moving semantic token definitions out of the web foundation or application stylesheet layer

### Requirement: Login/logout control is a widget feature
The system SHALL provide a `login` widget feature that renders the appropriate authentication action for the current request state when auth is available and the feature is not disabled.

#### Scenario: Login action renders for anonymous requests
- **WHEN** auth is available to the composed site
- **AND** the `login` feature is not disabled
- **AND** the current request has no authenticated user
- **THEN** widget-aware templates render a login button
- **AND** the login button links to the route named `auth:login`

#### Scenario: Logout action renders for authenticated requests
- **WHEN** auth is available to the composed site
- **AND** the `login` feature is not disabled
- **AND** the current request has an authenticated user with an email address
- **THEN** widget-aware templates render a default profile avatar followed by a logout button
- **AND** the logout button links to the route named `auth:logout`

#### Scenario: Default avatar uses email initial
- **WHEN** the login widget renders an authenticated user without a profile image
- **THEN** the widget receives profile image display data from a public auth-owned descriptor
- **AND** the descriptor supports an image source when one is available
- **AND** the descriptor supports fallback text when no image source is available
- **AND** the fallback text may use the first character of the user's email address, capitalised
- **AND** the avatar is rendered without requiring profile-image storage or profile module support

#### Scenario: Login widget can be disabled
- **WHEN** the `login` widget feature is disabled
- **THEN** widget-aware templates do not render the login/logout control

#### Scenario: Auth dependency is absent
- **WHEN** no auth capability, auth request context, or auth route surface is available from the composed site
- **THEN** widget-aware templates do not render the login/logout control by default
- **AND** startup does not fail solely because auth is absent

### Requirement: Header widget actions have deterministic ordering
The system SHALL place enabled header widgets in a deterministic order so authentication controls and theme controls do not depend on template accidents.

#### Scenario: Login control appears before theme control
- **WHEN** auth is available
- **AND** both the `login` widget feature and theme selector widget feature are enabled
- **THEN** the login/logout control is rendered flush right in the header action area
- **AND** it appears immediately to the left of the theme selector control

#### Scenario: Header widgets remain overridable
- **WHEN** an earlier configured application module overrides the login widget partial or header action layout
- **THEN** the application override is used according to normal Wybra template precedence

### Requirement: Login widget is responsive
The system SHALL provide responsive behaviour for the login/logout control so it remains usable on narrow screens, using responsive conventions supplied by the web foundation.

#### Scenario: Anonymous mobile layout centres login action
- **WHEN** the viewport uses the mobile header layout
- **AND** the current request is anonymous
- **THEN** the login button remains centred within its compact control area

#### Scenario: Authenticated mobile layout hides avatar
- **WHEN** the viewport uses the mobile header layout
- **AND** the current request is authenticated
- **THEN** the profile avatar is not displayed
- **AND** the logout button remains centred within its compact control area

### Requirement: Login widget consumes profile image descriptors
The system SHALL have the login widget consume profile-owned image descriptors when rendering authenticated user avatar data.

#### Scenario: Profile capability provides avatar data
- **WHEN** the login widget renders an authenticated user
- **AND** the profile capability is available
- **THEN** the widget obtains profile image display data from profile
- **AND** renders the returned image source or fallback text

#### Scenario: Profile capability is unavailable
- **WHEN** the login widget renders an authenticated user
- **AND** the profile capability is not available
- **THEN** the widget does not depend on auth-owned profile image helpers
- **AND** it renders only behaviour that can be provided without profile data
