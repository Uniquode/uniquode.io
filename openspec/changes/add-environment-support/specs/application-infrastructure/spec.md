## MODIFIED Requirements

### Requirement: ASGI application shell
The system SHALL provide a FastAPI/Starlette ASGI application shell with an application factory and stable ASGI app import path.

#### Scenario: Application can be imported
- **WHEN** a developer imports the documented ASGI app path
- **THEN** the import returns an ASGI-compatible application object using
  default environment-backed settings without requiring product configuration
  or database state

#### Scenario: Application can be constructed for tests
- **WHEN** tests call the application factory with explicit settings
- **THEN** a fresh FastAPI application instance is returned with those settings
  and baseline routes registered
