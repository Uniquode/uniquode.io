## Why

Wevra applications should be simple to create and reason about once module configuration is chosen. Wevra needs a single extensible generator command so site and module templates can be created consistently from Wevra-owned conventions.

This change introduces `wevra-create` as an extensible generator command. The first required generator is `wevra-create site`; future subcommands should create modules and other project artefacts from the same extensible command surface.

## What Changes

- Add a general `wevra-create` command designed around extensible subcommands and templates. The first implemented subcommand is `site`, shaped around:
  - `wevra-create site --name <name> --title <title> ...`
  - future options for configured modules, auth/database inclusion, output package names, config file generation, and template selection.
- Generate a minimal host application from scratch, including the expected app-owned files such as:
  - `app.py` or the requested app module name
  - `context.py`
  - `settings.py`
  - `routes.py`
  - `views.py`
  - generated config such as `app.toml` where requested
- Add an extensible generator model so `wevra-create` can create additional artefact types without redesigning the command.
- Add an initial direction for application module generation, including a `crud` or data-management pattern for simple database-backed management screens and reports.
- Keep module generation open-ended so future module templates and project artefact generators can be added under the same command.

## Capabilities

### New Capabilities

- `site-generator`: Defines the `wevra-create site` command, generated site structure, supported options, and config generation.
- `module-generator`: Defines the extensible `wevra-create` generation model for application modules, including an initial CRUD/data-management module template direction and future template expansion.

### Modified Capabilities

- `module-settings-access`: Aligns generated site/module output with type-keyed capabilities and public module helpers.

## Impact

- Adds a new extensible Wevra CLI surface: `wevra-create`.
- Adds generated project/site templates and a generation contract for future templates.
- Requires tests for generated site structure, generated config, generated startup behaviour, and extensible template dispatch.
