## 1. Rename Inventory

- [x] 1.1 Capture pre-rename `wevra`, `Wevra`, and `WEVRA` references using hidden-file-aware search.
- [x] 1.2 Confirm inventory excludes all `.git` directories, `openspec/changes/archive/**`, and `openspec/changes/rename-wevra-wybra/**`.
- [x] 1.3 Identify filesystem paths that require renaming in the root workspace and nested package checkout.

## 2. Package and Workspace Rename

- [x] 2.1 Rename nested package source, test, metadata, and documentation paths from `wevra` to `wybra`.
- [x] 2.2 Update root workspace dependency, source mapping, and lockfile/install state from `wevra` to `wybra`.
- [x] 2.3 Update Python imports, package metadata, entry points, command names, and repository/source links.
- [x] 2.4 Update configuration namespaces from `[wevra.*]` to `[wybra.*]`.
- [x] 2.5 Update module identifiers from `wevra.*` to `wybra.*`.

## 3. OpenSpec and Documentation Rename

- [x] 3.1 Update accepted specs under `openspec/specs/**`.
- [x] 3.2 Update all active OpenSpec changes except `rename-wevra-wybra`.
- [x] 3.3 Preserve all archived OpenSpec changes without edits.
- [x] 3.4 Update ADRs and repository documentation.
- [x] 3.5 Add concise Wybra name-origin context to the renamed package README.

## 4. Developer Tooling

- [x] 4.1 Move root `.bin/` shortcut aliases into the renamed Wybra project.
- [x] 4.2 Retarget shortcut aliases from `wevra-*` to `wybra-*`.
- [x] 4.3 Update shortcut helper text and paths such as `git-status`.

## 5. Audit and Validation

- [x] 5.1 Audit remaining `wevra`, `Wevra`, and `WEVRA` references outside excluded paths.
- [x] 5.2 Manually classify or fix all remaining references.
- [x] 5.3 Run OpenSpec validation.
- [x] 5.4 Run nested package checks.
- [x] 5.5 Run root workspace checks.
- [ ] 5.6 Verify remotes and tracked GitHub/source links after the repository rename is coordinated.
