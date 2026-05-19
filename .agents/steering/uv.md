# uv Workflow

Use `uv` as the project manager and tool runner.

Project initialization must create `pyproject.toml` through `uv`, not by writing the file directly. This lets `uv` perform related setup such as Git repository initialization.

Dependency changes must use project metadata:

- Use `uv add <package>` for runtime dependencies.
- Use `uv add --dev <package>` or the appropriate dependency group option for development dependencies.
- Do not use `uv pip install` or other `uv pip` commands that mutate the virtual environment.
- Read-only `uv pip` inspection commands are allowed.

Run Python commands through the project environment with `uv run`. Any command that depends on the virtual environment or project-installed packages must be prefixed with `uv run`, including Python scripts, pytest, Ruff, `ty check src/`, and other development tools.
