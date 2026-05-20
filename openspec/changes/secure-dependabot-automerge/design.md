## Context

The repository already has a `Tests` GitHub Actions workflow and Dependabot configuration for GitHub Actions and Python dependencies. Branch protection is enabled for `main`, but the dependency update process still needs explicit safety gates before any automated merge policy is introduced.

This is an administrative security change. It affects repository automation and protection settings, not application architecture or runtime behaviour. No ADR is required at this time.

## Goals / Non-Goals

**Goals:**

- Keep GitHub Actions and Python dependencies monitored by Dependabot.
- Enable auto-merge only for Dependabot semver patch updates.
- Require successful CI and security checks before any auto-merge can complete.
- Add CodeQL analysis for the Python codebase and include it in the required merge checks.
- Include an available secret-scanning PR check, such as GitGuardian or GitHub secret scanning, in the required merge checks.
- Keep update policy conservative and auditable.

**Non-Goals:**

- Do not auto-merge minor, major, or grouped security updates in this change.
- Do not bypass branch protection, required checks, or review requirements.
- Do not introduce application runtime dependencies.
- Do not define a long-term security architecture ADR.

## Decisions

### Dependabot Configuration

Use `.github/dependabot.yml` to monitor the `github-actions` and `uv` ecosystems on a daily schedule.

Rationale: GitHub officially supports both ecosystems for Dependabot version updates. Daily checks keep security and patch PR latency low without requiring custom dependency polling.

Alternative considered: Use only Dependabot security updates. This would reduce routine PR volume but would allow non-vulnerable patch drift to accumulate and make later security remediation noisier.

### Auto-Merge Mechanism

Use a separate GitHub Actions workflow that runs on Dependabot pull requests, fetches Dependabot metadata, and requests GitHub auto-merge only when `update-type` is `version-update:semver-patch`.

Rationale: `dependabot.yml` does not provide auto-merge behaviour. GitHub's documented pattern is to use Actions plus `dependabot/fetch-metadata` and the GitHub CLI or API to enable auto-merge.

Alternative considered: Use deprecated Dependabot comment commands. These are no longer the preferred path and should not be used for new automation.

### Merge Safety Gate

Branch protection or repository rulesets must remain the enforcement layer for successful checks. The auto-merge workflow only marks an eligible PR for auto-merge; it must not merge directly in a way that bypasses required checks.

Rationale: This keeps merge safety centralised in repository protection rather than duplicating check logic in the workflow.

Alternative considered: Have the workflow inspect check conclusions and merge directly. That is more brittle and risks drift from branch protection settings.

### Required Checks

Require the existing test workflow check, CodeQL, and the configured secret-scanning PR check before merges to `main`.

Rationale: Auto-merged dependency updates should be held to the same quality and security standard as human-authored PRs.

Alternative considered: Require only test CI for patch updates. That would miss classes of security regressions that static analysis and secret scanning are meant to catch.

### GitHub Actions Updates

Keep GitHub Actions updates monitored by Dependabot, but do not automatically merge them until explicitly allowed by a later policy.

Rationale: Workflow dependency updates can affect CI and security automation itself, so they deserve human review at the start.

Alternative considered: Auto-merge all patch updates across all ecosystems. This is simpler, but it applies the same trust level to code dependencies and workflow automation dependencies.

## Risks / Trade-offs

- Required checks may not be selectable until they have run recently in GitHub. Mitigation: add workflows first, let them report on a PR, then update branch protection.
- Dependabot patch updates can still introduce regressions. Mitigation: keep branch protection checks required and limit auto-merge to patch updates.
- CodeQL can produce initial findings that block auto-merge. Mitigation: resolve or explicitly triage findings before requiring the check.
- Secret scanning provider behaviour depends on repository settings or external app installation. Mitigation: verify whether GitGuardian or GitHub secret scanning is active before making its check required.
- Grouped Dependabot PRs may contain updates with mixed risk. Mitigation: do not auto-merge grouped security, minor, or major updates in this change.

## Migration Plan

1. Add or confirm Dependabot configuration for GitHub Actions and `uv`.
2. Add CodeQL scanning for Python or enable GitHub default setup.
3. Confirm the available secret scanning provider and PR check name.
4. Let the test, CodeQL, and secret scanning checks report at least once.
5. Update branch protection or rulesets for `main` to require those checks.
6. Add the Dependabot auto-merge workflow for semver patch updates.
7. Validate the workflow YAML and repository protection behaviour with a Dependabot patch PR.

Rollback is to disable or remove the auto-merge workflow. Dependabot PR creation, required checks, and security scanning can remain in place independently.

## Open Questions

- Which secret scanning check will be required: GitGuardian, GitHub secret scanning, or both?
- Should GitHub Actions patch updates be eligible for auto-merge after an initial observation period?
- Should patch updates for production and development dependencies have different auto-merge policies?
