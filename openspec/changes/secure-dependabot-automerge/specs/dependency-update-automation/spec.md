## ADDED Requirements

### Requirement: Dependency ecosystems are monitored
The repository SHALL configure Dependabot version update monitoring for GitHub Actions and Python dependencies managed by `uv`.

#### Scenario: GitHub Actions ecosystem is monitored
- **WHEN** Dependabot reads repository configuration
- **THEN** it monitors GitHub Actions workflow dependencies from the repository root

#### Scenario: Python ecosystem is monitored
- **WHEN** Dependabot reads repository configuration
- **THEN** it monitors the `uv` Python dependency ecosystem from the repository root

### Requirement: Patch dependency updates can auto-merge
The repository SHALL provide automation that enables GitHub auto-merge for Dependabot pull requests containing semver patch version updates.

#### Scenario: Patch update is eligible
- **WHEN** Dependabot opens a pull request whose update type is `version-update:semver-patch`
- **THEN** repository automation enables GitHub auto-merge for that pull request

#### Scenario: Minor update is not auto-merged
- **WHEN** Dependabot opens a pull request whose update type is `version-update:semver-minor`
- **THEN** repository automation does not enable GitHub auto-merge for that pull request

#### Scenario: Major update is not auto-merged
- **WHEN** Dependabot opens a pull request whose update type is `version-update:semver-major`
- **THEN** repository automation does not enable GitHub auto-merge for that pull request

### Requirement: Auto-merge respects required checks
The repository SHALL rely on branch protection or repository rulesets so auto-merge completes only after required checks pass.

#### Scenario: Required checks are pending or failing
- **WHEN** a Dependabot patch pull request has pending or failing required checks
- **THEN** GitHub auto-merge does not merge the pull request

#### Scenario: Required checks pass
- **WHEN** a Dependabot patch pull request has all required checks passing
- **THEN** GitHub auto-merge may merge the pull request according to repository merge policy

### Requirement: Test CI is a required merge gate
The repository SHALL require the test workflow check before pull requests can merge to `main`.

#### Scenario: Test workflow fails
- **WHEN** a pull request targets `main` and the test workflow check fails
- **THEN** the pull request cannot merge

### Requirement: CodeQL is a required merge gate
The repository SHALL run CodeQL analysis for the Python codebase and require the CodeQL check before pull requests can merge to `main`.

#### Scenario: CodeQL check fails
- **WHEN** a pull request targets `main` and the CodeQL check fails
- **THEN** the pull request cannot merge

### Requirement: Secret scanning is a required merge gate
The repository SHALL require the configured secret-scanning PR check before pull requests can merge to `main`.

#### Scenario: Secret scanning check fails
- **WHEN** a pull request targets `main` and the configured secret-scanning check fails
- **THEN** the pull request cannot merge

#### Scenario: Secret scanning provider is not yet confirmed
- **WHEN** the repository does not yet have a confirmed secret-scanning PR check
- **THEN** implementation records the provider decision before making the check required
