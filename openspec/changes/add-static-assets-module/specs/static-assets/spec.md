## ADDED Requirements

### Requirement: Static assets have a dedicated module boundary
The system SHALL provide static asset infrastructure through a dedicated Wevra static module rather than embedding static-specific behaviour in the web rendering module.

#### Scenario: Static assets are configured
- **WHEN** an application configures static asset serving or collection
- **THEN** Wevra exposes that behaviour through the static asset module boundary
- **AND** web rendering remains focused on routes, templates, forms, CSRF, security headers, and errors

#### Scenario: Static serving is suppressed
- **WHEN** application static serving is disabled
- **THEN** Wevra does not mount an app-served static file handler
- **AND** static URLs remain available for deployments that serve static assets externally

#### Scenario: Static assets are collected
- **WHEN** static asset collection is requested
- **THEN** Wevra discovers configured module static sources with deterministic precedence
- **AND** duplicate or shadowed static assets are reported clearly
