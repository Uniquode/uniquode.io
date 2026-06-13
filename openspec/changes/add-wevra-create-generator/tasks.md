## 1. CLI Structure

- [ ] 1.1 Add the `wevra-create` command entry point in Wevra package metadata.
- [ ] 1.2 Implement explicit subcommand dispatch for generator commands.
- [ ] 1.3 Add help and error output for supported and unsupported generator subcommands.

## 2. Site Generator

- [ ] 2.1 Define the first-pass `wevra-create site` options, including name, title, output path, module list, and config generation choices.
- [ ] 2.2 Implement deterministic site file generation for app startup, context, settings, routes, and views.
- [ ] 2.3 Generate optional app config from requested module/config choices.
- [ ] 2.4 Ensure generated site code uses public Wevra startup APIs and contains no app-owned Wevra environment/config boilerplate.
- [ ] 2.5 Add collision detection so existing files are not overwritten without an explicit option.

## 3. Generator Extensibility

- [ ] 3.1 Extract shared generator request/output/path handling so new generator types can reuse it.
- [ ] 3.2 Add an internal generator registry or dispatch table for future generator templates.
- [ ] 3.3 Define the module generator contract for future application module templates.

## 4. Module Template Direction

- [ ] 4.1 Add the initial module-template structure for generated modules using Wevra public module boundaries.
- [ ] 4.2 Document the intended CRUD/data-management module template shape without making it part of basic site generation.
- [ ] 4.3 Ensure generated module examples use async `setup_site(site)` and module-owned config definitions where applicable.

## 5. Tests And Documentation

- [ ] 5.1 Add tests for `wevra-create` dispatch and help/error behaviour.
- [ ] 5.2 Add tests for generated site file structure and generated config content.
- [ ] 5.3 Add tests proving generated site code excludes app-owned environment/config aggregation boilerplate.
- [ ] 5.4 Add tests for collision handling and explicit overwrite/update behaviour.
- [ ] 5.5 Document `wevra-create site` usage and the generator extension direction.
