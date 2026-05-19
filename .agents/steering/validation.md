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

When running commands through the agent environment, use `gtimeout` for commands that could hang:

```text
gtimeout 30s uv run ruff format
gtimeout 30s uv run ruff check
gtimeout 30s uv run ty check src/
gtimeout 30s uv run pytest
```
