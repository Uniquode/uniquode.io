# Wybra Workspace

This repository is the local `uv` workspace for the Uniquode application.
`wybra` is consumed as a framework dependency and, for now, may be present as
an ignored editable checkout.

The workspace members are:

- `app/` - the concrete Uniquode application project
- `wybra/` - a temporary ignored editable checkout used only while the
  framework dependency is not yet resolved as a regular published or pinned
  dependency

The Wybra framework source repository is
<https://github.com/Uniquode/wybra>.

While `wybra/` is an ignored editable checkout, changes may intentionally span
this repository and a matching `Uniquode/wybra` branch. When reviewing an
application branch that imports new Wybra APIs, treat the matching Wybra branch
as part of the change and merge or pin it before merging the application
branch. A clean checkout that resolves Wybra from `main` can otherwise fail
until the framework side has landed.

Use the workspace root for shared dependency resolution while `wybra/` is a
local workspace member:

```sh
uv lock
uv sync --all-packages
```

Run application validation from this repository:

```sh
uv sync --package app
uv --directory app run pytest -q
uv run ruff check app/src app/tests
```

Running `uv` from the app member discovers this workspace root, so the single
root lock remains authoritative for the application and its temporary local
Wybra dependency source.

Run application tests with the app member as the working directory, either by
changing directory first or by using `uv --directory app ...`. Some project
tools intentionally derive the host project from the current working directory.

Do not run Wybra-owned tests, linting, or type checks from this repository.
Those checks belong to the `wybra` repository. Once `wybra` is available as a
regular dependency, remove the ignored local `wybra/` checkout from this
workspace.
