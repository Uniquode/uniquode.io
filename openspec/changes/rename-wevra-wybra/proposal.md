## Why

The Wevra package, repository, CLI, configuration namespace, and documentation
are still unpublished, so the project can rename them without compatibility
aliases or migration shims. `wybra` has a cleaner collision profile than the
other reviewed candidates while preserving the intended Bundjalung-related
source thread around fire, wood, and firewood.

## What Changes

- **BREAKING** Rename current, forward-looking tracked-worktree references
  from Wevra/wevra/WEVRA to Wybra/wybra/WYBRA where they name the project,
  package, modules, CLI, configuration, routes, docs, specs, ADRs, tests,
  workflows, and metadata.
- Leave archived OpenSpec changes unchanged because they are historical records.
- Leave the `rename-wevra-wybra` change identifier and directory name unchanged
  so the change remains traceable to the transition it describes.
- Rename all other active OpenSpec changes where they refer to the library
  going forward, so open planning artifacts clearly identify the `wybra`
  package and repository. Exclude only this `rename-wevra-wybra` change from
  that active-change rewrite.
- Rename accepted OpenSpec specs under `openspec/specs/**` where they refer to
  the library going forward.
- **BREAKING** Rename the Python package/module namespace from `wevra` to
  `wybra`.
- **BREAKING** Rename CLI commands from `wevra-*` to `wybra-*`.
- **BREAKING** Rename configuration namespaces such as `[wevra.*]` to
  `[wybra.*]`.
- **BREAKING** Rename module identifiers such as `wevra.media` and
  `wevra.profile` to `wybra.media` and `wybra.profile`.
- Rename repository/package metadata, documentation, OpenSpec, and ADR
  references to the new name.
- Update the renamed package README to briefly explain the origin of the
  `wybra` name, including the Bundjalung/neighbouring dialect records and the
  fire, firewood, or wood meaning.
- Update the root workspace dependency and source mapping from `wevra` to
  `wybra`.
- Move the root `.bin/` developer shortcut directory into the renamed `wybra`
  project, because those scripts are optional convenience aliases for the
  package-owned `wybra-*` commands rather than root application tooling.
- Rename `.bin/` shortcut targets from `wevra-*` to `wybra-*` and update helper
  text or paths such as the current `git-status` script's Wevra checkout
  references.
- Rename the GitHub repository from `wevra` to `wybra` and update tracked
  repository URLs, source links, docs, and lockfile references accordingly.
- Do not add compatibility aliases, compatibility imports, legacy config
  fallbacks, or old CLI entry points unless a later explicit requirement
  introduces a published-consumer compatibility need.

## Capabilities

### New Capabilities

### Modified Capabilities

- `application-infrastructure`: Project metadata, workspace dependency names,
  repository references, and package/module naming requirements change from
  Wevra to Wybra.
- `site-startup-api`: Configured module identifiers and module discovery names
  change from the `wevra.*` namespace to the `wybra.*` namespace.
- `environment-configuration`: Configuration sections and environment-facing
  project namespace names change from `wevra.*` to `wybra.*`.
- `auth-management-cli`: CLI command names change from `wevra-*` to `wybra-*`
  where the command belongs to the renamed package.
- `developer-tooling`: Optional local shortcut aliases for package commands move
  from the root project `.bin/` directory into the renamed Wybra project and
  target `wybra-*` commands.
- `web-foundation`: Web module imports, route/resource identifiers, template
  context naming, and documentation references change to the Wybra namespace.
- `web-widgets`: Widget module identifiers, imports, resource references, and
  configuration examples change to the Wybra namespace.
- `module-settings-access`: Module settings examples and module-owned
  configuration names change to the Wybra namespace.
- `project-maintenance`: Project documentation and validation guidance changes
  to use the new package, CLI, repository, and workspace names.

## Impact

- Affects current tracked files containing `wevra`, `Wevra`, or `WEVRA`,
  including Python imports, package directories, scripts, tests, templates,
  configuration, docs, active OpenSpec changes, accepted specs, ADRs, workflow
  files, metadata, and lockfiles.
- Affects active OpenSpec changes other than `rename-wevra-wybra`, and accepted
  specs under `openspec/specs/**`.
- Does not affect archived OpenSpec changes or the `rename-wevra-wybra` change
  path/name itself, except for content needed to describe the rename accurately.
- Requires coordinated root workspace and nested package repository changes.
- Moves root-owned `.bin/` tracked files into the Wybra repository so developer
  opt-in shortcut installation follows the package that owns the corresponding
  commands.
- Requires a GitHub repository rename and follow-up verification of remotes,
  GitHub Actions, Dependabot, CodeQL, Sourcery, GitGuardian, package metadata,
  and any tracked source/documentation links.
- Requires filesystem renames for package directories and possibly the local
  workspace checkout directory.
- Requires full validation after rename to catch missed text references,
  import paths, entry points, config namespaces, and generated lockfile data.
