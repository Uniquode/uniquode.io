#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any

WYBRA_GIT_URL = "https://github.com/Uniquode/wybra.git"
GIT_SOURCE = {"git": WYBRA_GIT_URL, "branch": "main"}
GIT_SOURCE_LINE = (
    'wybra = { git = "https://github.com/Uniquode/wybra.git", branch = "main" }'
)
PATH_SOURCE_LINE = 'wybra = { path = "../wybra", editable = true }'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ensure uniquode.io uses the commit-safe Wybra Git source.",
    )
    parser.add_argument(
        "mode",
        choices=("check", "normalise-git"),
        help="'check' validates pyproject.toml; 'normalise-git' rewrites path mode.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="pyproject.toml path. Defaults to the current directory.",
    )
    args = parser.parse_args(argv)

    if args.mode == "normalise-git":
        normalise_git_source(args.pyproject)
        return 0

    if is_git_source(args.pyproject):
        return 0

    print(
        "pyproject.toml must use the Wybra Git source.",
        file=sys.stderr,
    )
    return 1


def normalise_git_source(pyproject_path: Path) -> None:
    if not is_git_source(pyproject_path):
        _rewrite_wybra_source_to_git(pyproject_path)
    if not is_git_source(pyproject_path):
        raise SystemExit("Failed to normalise pyproject.toml to the Wybra Git source.")


def is_git_source(pyproject_path: Path) -> bool:
    return _wybra_source(pyproject_path) == GIT_SOURCE


def _wybra_source(pyproject_path: Path) -> object:
    data = _read_toml(pyproject_path)
    return data.get("tool", {}).get("uv", {}).get("sources", {}).get("wybra")


def _read_toml(pyproject_path: Path) -> dict[str, Any]:
    if not pyproject_path.is_file():
        raise SystemExit(f"Expected pyproject configuration at: {pyproject_path}")
    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))


def _rewrite_wybra_source_to_git(pyproject_path: Path) -> None:
    lines = pyproject_path.read_text(encoding="utf-8").splitlines()
    source_range = _uv_sources_range(lines)
    wybra_source_indices = [
        index for index in source_range if _is_wybra_source_line(lines[index])
    ]
    if not wybra_source_indices:
        raise SystemExit("pyproject.toml does not contain a Wybra source line.")

    insert_at = wybra_source_indices[0]
    for index in reversed(wybra_source_indices):
        del lines[index]
    lines.insert(insert_at, GIT_SOURCE_LINE)
    lines.insert(insert_at + 1, f"# {PATH_SOURCE_LINE}")
    pyproject_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _uv_sources_range(lines: list[str]) -> range:
    start = None
    for index, line in enumerate(lines):
        if line.strip() == "[tool.uv.sources]":
            start = index + 1
            break
    if start is None:
        raise SystemExit("pyproject.toml does not contain [tool.uv.sources].")

    stop = len(lines)
    for index in range(start, len(lines)):
        line = lines[index].strip()
        if line.startswith("[") and line.endswith("]"):
            stop = index
            break
    return range(start, stop)


def _is_wybra_source_line(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("#"):
        stripped = stripped[1:].strip()
    return stripped.startswith("wybra") and stripped.removeprefix(
        "wybra"
    ).lstrip().startswith("=")


if __name__ == "__main__":
    raise SystemExit(main())
