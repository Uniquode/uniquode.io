## Context

Wevra startup and module composition are moving toward a small host-app surface: create or own a FastAPI instance, configure Wevra startup, then focus on product routes and views. A developer should be able to create that shape from scratch without copying internal Wevra boilerplate.

`wevra-create` is the generator command for this. It must start with `wevra-create site`, but it must be extensible because future generators will create application modules, CRUD/data-management modules, reports, and other project artefacts.

## Goals / Non-Goals

**Goals:**

- Add one extensible `wevra-create` command surface.
- Implement the first subcommand, `wevra-create site`.
- Generate a minimal, idiomatic Wevra host app using Wevra-owned startup and config conventions.
- Generate only app-owned files for a site: app entry point, context, settings, routes, views, and optional config.
- Establish a generator extension model for future module and CRUD/data-management templates.
- Keep generated code free of app-owned Wevra config/environment boilerplate.

**Non-Goals:**

- Implement every future generator template in the first pass.
- Generate compatibility code for older app-side startup/configuration patterns.
- Require auth, database, or any specific Wevra feature module in generated sites.
- Add a large scaffolding framework before concrete generator requirements need it.

## Decisions

### Use a single command with subcommands

`wevra-create` will be the stable command. `site` is the first subcommand, and future subcommands such as module or CRUD generators will plug into the same command tree.

Alternative considered: separate commands such as `wevra-create-site`. That would fragment the interface and make future generators harder to discover, so it is rejected.

### Keep generator dispatch explicit and small

The first implementation will use an explicit internal registry or command dispatch table for generator subcommands. This gives extension points without introducing plugin discovery or dynamic loading until there is a requirement.

Alternative considered: entry-point plugin discovery immediately. That adds lifecycle and packaging complexity before external generators are required, so it is deferred.

### Generate pristine host app structure

The site generator will emit the minimal app-owned files needed to run a site. It will not generate app-owned `environment.py`, Wevra config definition aggregation, auth/database setup code, route discovery code, static/template composition, or validation boilerplate.

Alternative considered: generate the current app layout exactly. That would codify leftover scaffolding that is being removed by `clean-app-pristine`, so it is rejected.

### Module generation is template-based and capability-aware

Future module generators will produce module surfaces that integrate with Wevra through public APIs: `setup_site(site)`, module route declarations, config definitions owned by the module, and capability helpers. CRUD/data-management templates will be one module template family, not a hard-coded special case in site generation.

Alternative considered: make CRUD generation part of `wevra-create site`. That couples site creation to database-backed management workflows and conflicts with optional database support, so it is rejected.

### Collision handling is explicit

Generators will fail before overwriting existing files unless the command has an explicit overwrite/update mode. Generated output must be predictable and reviewable.

Alternative considered: silently overwrite files for convenience. That is unsafe for application source and makes generator runs hard to reason about, so it is rejected.

## Risks / Trade-offs

- [Risk] Generator templates can drift from current Wevra startup conventions. → Add tests that generated code contains the expected public startup API and excludes old boilerplate.
- [Risk] Extensibility can become over-engineered. → Start with a small internal registry and defer external plugin loading.
- [Risk] Generated CRUD modules could imply a database requirement for all sites. → Keep CRUD under module generation and require database configuration only when that module template is selected.
- [Risk] Generated files may not match future cleaned app baseline. → Coordinate generated templates with `clean-app-pristine` and update templates after the app boundary is finalised.

## Migration Plan

1. Add the `wevra-create` CLI entry point in Wevra.
2. Implement subcommand dispatch and the `site` generator.
3. Add file templates for the minimal site shape.
4. Add collision detection and deterministic output rules.
5. Add tests for generated file structure, generated config, and generator dispatch.
6. Add initial module generator contracts and defer richer templates to follow-up tasks when needed.

## Open Questions

- Which exact options should `wevra-create site` expose in the first shipped pass beyond `--name`, `--title`, output path, and config generation?
- Should generated sites default to including `wevra.web`, or should even web module inclusion be explicit in generated config?
