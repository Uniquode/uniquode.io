## MODIFIED Requirements

### Requirement: Persistence conventions
The system SHALL establish SQLAlchemy async persistence conventions with Alembic migrations without coupling route handlers directly to database clients.

#### Scenario: Persistence location is defined
- **WHEN** a developer inspects the project package
- **THEN** there is a clear package location or documented boundary for SQLAlchemy async models, session configuration, and Alembic migrations

#### Scenario: Routes are not coupled to database clients
- **WHEN** the route modules are inspected
- **THEN** route handlers do not directly instantiate or depend on database clients

#### Scenario: PostgreSQL and SQLite remain supported
- **WHEN** a developer inspects persistence configuration
- **THEN** PostgreSQL is supported for production and SQLite is supported for local development and lightweight tests where behaviour remains portable

### Requirement: Dependency discipline
The system SHALL limit runtime dependencies to platform and product dependencies justified by accepted OpenSpec requirements.

#### Scenario: Runtime dependencies are requirement-scoped
- **WHEN** a developer reviews runtime dependencies
- **THEN** they are limited to accepted FastAPI/Starlette, Jinja2, ASGI, SQLAlchemy async, Alembic, FastAPI Users, and requirement-backed product needs

#### Scenario: Dependencies are added through uv project metadata
- **WHEN** dependencies are added during implementation
- **THEN** runtime dependencies are added with `uv add` and development dependencies are added with `uv add --dev` or an appropriate dependency group option

#### Scenario: Virtual environment is not mutated outside project metadata
- **WHEN** implementation needs package inspection
- **THEN** read-only `uv pip` commands are allowed, but `uv pip install` and other `uv pip` commands that modify the virtual environment are not used

#### Scenario: Unrequired product dependencies are excluded
- **WHEN** dependency changes are reviewed
- **THEN** they do not add asset pipeline, queue, NoSQL, or product-specific integration dependencies without a requirement

### Requirement: Validation command explainability
The system SHALL keep quick validation output concise while offering a verbose mode that explains the checks being performed.

#### Scenario: Default validation output remains concise
- **WHEN** a developer runs the validation command without verbosity
- **THEN** the command reports per-target success or failure without listing every individual check

#### Scenario: Verbose validation output lists checks
- **WHEN** a developer runs the validation command with verbose output enabled
- **THEN** the command lists the concrete checks performed for each target, including relevant paths, route/template checks, asset checks, and persistence checks

### Requirement: Server-rendered form CSRF protection
The system SHALL protect all server-rendered form submissions with a shared CSRF mechanism rather than per-view ad hoc checks.

#### Scenario: Form pages receive CSRF tokens
- **WHEN** the application renders a server-owned HTML page or fragment that contains a POST form
- **THEN** the rendered form includes a CSRF field derived from the shared form-security boundary

#### Scenario: Form submissions are checked before view handling
- **WHEN** a browser submits a server-rendered form through a page or partial route
- **THEN** the HTML dispatcher validates the submitted CSRF token before the route view can perform state-changing work

#### Scenario: Non-form unsafe requests can provide a CSRF header
- **WHEN** a page or partial route receives an unsafe method from htmx or custom
  JavaScript without a form field payload
- **THEN** the HTML dispatcher can validate the configured CSRF token from a
  request header instead of requiring a form field

#### Scenario: Invalid CSRF submissions are rejected
- **WHEN** a form submission omits, tampers with, or mismatches the CSRF token
- **THEN** the application rejects the request without issuing authentication cookies or performing the requested state change

#### Scenario: CSRF signing seed is configurable
- **WHEN** the application constructs the CSRF token signer
- **THEN** it uses an application setting for the signing secret, with local development allowed to generate a startup-local secret until environment-backed configuration is introduced

#### Scenario: Non-local CSRF signing seed is stable
- **WHEN** the application is configured for a non-local deployment
- **THEN** the CSRF signing secret must be explicitly configured and non-blank so tokens remain valid across app processes and restarts

#### Scenario: Non-local CSRF cookie transport is secure
- **WHEN** the application is configured for a non-local deployment
- **THEN** CSRF nonce cookies are marked `Secure` so they are not sent over
  plaintext HTTP
