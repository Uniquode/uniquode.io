# Validation

Baseline validation commands:

```text
uv run ruff format
uv run ruff check
uv run ty check src/
uv run pytest
openspec validate <change> --strict
```

The baseline type check targets source code. Tests are covered by pytest and Ruff.

When running commands through the agent environment, use `gtimeout` selectively for commands that could realistically hang, block on I/O, or start long-running processes. Do not add `gtimeout` by default to every `uv run` command.

Typical commands that usually do not need `gtimeout`:

```text
uv run ruff format --check
uv run ruff check
uv run ty check src/
openspec validate <change> --strict
openspec validate --specs --strict
```

Use `gtimeout` for commands with meaningful hang risk, such as test suites, pre-commit runs, server processes, watchers, or other long-running commands:

```text
gtimeout 30s uv run pytest
gtimeout 120s uv run pre-commit run --all-files
gtimeout 30s uv run runserver
```
