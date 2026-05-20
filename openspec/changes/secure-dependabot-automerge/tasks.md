## 1. Dependency Monitoring

- [x] 1.1 Refresh existing test workflow action versions where needed.
- [x] 1.2 Add Dependabot configuration for the GitHub Actions ecosystem.
- [x] 1.3 Add Dependabot configuration for the `uv` Python dependency ecosystem.
- [x] 1.4 Confirm Dependabot alerts and Dependabot security updates are enabled in repository settings.

## 2. Code Scanning Gates

- [x] 2.1 Add CodeQL scanning for the Python codebase or enable GitHub CodeQL default setup.
- [x] 2.2 Let CodeQL report successfully on a pull request so the check can be selected as required.
- [x] 2.3 Add the CodeQL check to the required checks for `main`.

## 3. Secret Scanning Gates

- [x] 3.1 Confirm whether GitGuardian, GitHub secret scanning, or both will provide the required secret-scanning PR check.
- [ ] 3.2 Configure the selected secret-scanning provider for pull request checks.
- [ ] 3.3 Let the secret-scanning check report successfully on a pull request so the check can be selected as required.
- [ ] 3.4 Add the selected secret-scanning check to the required checks for `main`.

## 4. Branch Protection

- [x] 4.1 Confirm the exact required check name for the existing test workflow.
- [x] 4.2 Add the test workflow check to the required checks for `main`.
- [x] 4.3 Confirm repository auto-merge is enabled.
- [x] 4.4 Confirm branch protection or rulesets prevent auto-merge from completing while required checks are pending or failing.

## 5. Dependabot Auto-Merge Workflow

- [x] 5.1 Add a GitHub Actions workflow that runs only for Dependabot pull requests.
- [x] 5.2 Fetch Dependabot metadata in the workflow.
- [x] 5.3 Enable GitHub auto-merge only when the update type is `version-update:semver-patch`.
- [x] 5.4 Exclude minor, major, grouped security, and GitHub Actions update PRs from auto-merge.
- [x] 5.5 Use the repository's selected merge method consistently.

## 6. Validation

- [x] 6.1 Run YAML validation or pre-commit checks for all changed GitHub workflow and Dependabot files.
- [x] 6.2 Run `openspec validate secure-dependabot-automerge --strict`.
- [ ] 6.3 Validate behaviour with a Dependabot patch PR or equivalent dry run.
- [x] 6.4 Update `.todo/context.md` with the final administrative security automation state.
