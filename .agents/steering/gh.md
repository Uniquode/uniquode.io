# GitHub Workflow

Prefer the built-in GitHub connector and tools for GitHub work when they cover the required operation.

Use built-in GitHub capabilities first for:

- Pull request metadata, summaries, and state checks.
- Pull request creation or updates when the connector supports the required fields.
- Branch lookup, branch creation, and branch ref updates.
- Commit status and check summaries.
- Enabling pull request auto-merge when the connector supports the case.

Use `gh` only when the built-in tools do not expose the needed capability or when exact CLI/API behaviour is required. Appropriate `gh` cases include:

- Repository administration settings, including branch protection and required checks.
- GitHub App installation state for organisations or repositories.
- Repository security settings such as Dependabot, code scanning, and secret scanning configuration.
- GitHub Actions workflow run lists, logs, reruns, and detailed check diagnostics.
- Operations where the connector lacks required inputs or returns insufficient detail.

When using `gh` for an operation that appears connector-capable, record the reason briefly in the working notes or user-facing update.

Never use `--no-gpg-sign` or `--no-verify` with Git commands.
