## ADDED Requirements

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
- **THEN** the application override is used according to normal Wevra template precedence

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
