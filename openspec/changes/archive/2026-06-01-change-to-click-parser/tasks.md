## 1. Dependency And Parser Setup

- [x] 1.1 Add Click as a direct runtime dependency with `uv add click`.
- [x] 1.2 Replace `runserver` argparse parsing with a Click command while preserving `--host`, `--port`, and `--reload`.
- [x] 1.3 Preserve `APP_RELOAD` fallback behaviour when `--reload` is not supplied.
- [x] 1.4 Replace `validate` argparse parsing with Click while preserving targets, override options, verbose output, and exit codes.
- [x] 1.5 Replace `migrate` argparse parsing with Click while preserving subcommands, revision arguments, database URL override placement, and exit codes.

## 2. Uvicorn Pass-Through

- [x] 2.1 Accept unprocessed Uvicorn arguments after `--` in the `runserver` command.
- [x] 2.2 Delegate pass-through arguments to Uvicorn's CLI parsing without reimplementing Uvicorn option handling.
- [x] 2.3 Document Nginx TLS-termination usage with `X-Forwarded-*` headers and trusted `--forwarded-allow-ips`.

## 3. CLI Consistency Review

- [x] 3.1 Evaluate whether `usermgr` should migrate to Click in this change or remain argparse-backed for a later dedicated change.
- [x] 3.2 Migrate `usermgr` to Click while preserving command names, flags, password input behaviour, output formats, and exit codes.

## 4. Verification

- [x] 4.1 Add or update tests for `runserver` defaults, reload fallback, and pass-through Uvicorn arguments.
- [x] 4.2 Add or update tests for `validate` parser compatibility and command output.
- [x] 4.3 Add or update tests for `migrate` parser compatibility, including command-level and subcommand-level database URL overrides.
- [x] 4.4 Add or update tests for direct Click dependency expectations if needed.
- [x] 4.5 Run focused CLI tests, linting, formatting checks, type checking, and the full test suite.
