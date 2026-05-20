## Why

Dependency update PRs should be created consistently and low-risk point releases should be able to flow through once repository safety checks pass. This reduces dependency drift and improves security response time without giving update automation permission to bypass CI or security gates.

## What Changes

- Add repository automation for Dependabot PRs that enables GitHub auto-merge for semver patch updates after required checks pass.
- Keep minor, major, and security-grouped updates available for manual review unless a later requirement expands the policy.
- Require the test workflow as a merge gate before auto-merge can complete.
- Add CodeQL scanning for the Python codebase and make it a required merge gate after the check has reported successfully.
- Confirm GitGuardian or GitHub secret scanning behaviour and make the available secret-scan PR check a required merge gate when present.
- Keep Dependabot configuration focused on GitHub Actions and Python dependency ecosystems.
- Do not add an ADR for this administrative security workflow change.

## External Tracking

- Linear: `UT-7`

## Capabilities

### New Capabilities

- `dependency-update-automation`: Repository dependency update monitoring, security scanning gates, and controlled auto-merge for eligible Dependabot patch updates.

### Modified Capabilities

None.

## Impact

- Adds or updates GitHub repository configuration under `.github/`.
- Adds repository-level branch protection or ruleset requirements for CI and security checks.
- Depends on GitHub Dependabot, GitHub Actions, CodeQL, and the configured secret scanning provider.
- Does not change application runtime code, Python package APIs, database behaviour, or product-facing functionality.
