## ADDED Requirements

### Requirement: Host application uses Wevra site startup
The host application SHALL use the public Wevra site startup API for Wevra-owned composition while retaining ownership of host-specific application behaviour.

#### Scenario: Host startup delegates Wevra concerns
- **WHEN** the host ASGI application is constructed
- **THEN** the host app creates or receives its FastAPI app instance
- **AND** delegates Wevra module, route, auth, database, and settings composition to Wevra startup

#### Scenario: Host app excludes Wevra internals
- **WHEN** the host app source is inspected
- **THEN** it does not construct Wevra auth runtime state, database runtime state, module route defaults, or module settings internals directly

#### Scenario: Host app keeps product routes
- **WHEN** product-specific pages or routes are required
- **THEN** they remain in the host app or host-owned modules
- **AND** they use Wevra through public startup and type-keyed capability APIs only

### Requirement: App tests respect Wevra ownership
The host application test suite SHALL cover app-owned integration with the Wevra site startup API without duplicating Wevra module internals.

#### Scenario: App tests startup integration
- **WHEN** the host app test suite validates startup
- **THEN** it asserts that app-owned routes and configuration integrate with the public Wevra startup API
- **AND** it does not test Wevra auth, database, settings, or route composition semantics as if they were app-owned

#### Scenario: Wevra tests framework composition
- **WHEN** framework startup composition semantics are tested
- **THEN** those tests live in the Wevra project or Wevra-owned test suite
- **AND** the host app tests only rely on the documented public API
