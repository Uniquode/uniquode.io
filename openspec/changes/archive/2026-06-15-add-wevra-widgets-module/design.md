## Context

Wevra sites are built from an ordered list of modules. That ordering already
controls route publication, template precedence, static resource precedence, and
context-provider contribution. The current HTML foundation provides low-level
web behaviour, but some UI support features are not truly foundational. The
theme mode selector is the clearest example: it is useful default UX, but it is
an optional page-layout component rather than core rendering infrastructure.

`wevra.widgets` introduces a dedicated module for this reusable UI support
layer. It should be included like any other module, typically immediately after
the application module. That gives the application first chance to override
templates while allowing widgets to supersede lower-level `wevra.web` defaults
with richer widget-aware layouts.

## Goals / Non-Goals

**Goals:**

- Add a `wevra.widgets` module that participates in normal Wevra module
  composition.
- Provide a small widget-feature infrastructure for enabling/disabling UI
  support features from configuration.
- Move the existing `auto`/`light`/`dark` theme mode selector into
  `wevra.widgets`.
- Allow widget features to contribute templates, partials, context providers,
  routes, and static assets through existing Wevra web mechanisms.
- Preserve application override control through module order and template
  precedence.
- Keep `wevra.web` focused on low-level web foundation concerns.

**Non-Goals:**

- Do not implement the login/user/logout widget in this change.
- Do not implement site navigation widgets in this change.
- Do not introduce a special widget override or template resolution mechanism.
- Do not make `wevra.widgets` depend directly on auth, database, or application
  internals.
- Do not force applications to use widget-provided layouts.

## Decisions

### Use module ordering as the override mechanism

`wevra.widgets` will publish templates and resources like any other configured
module. It may provide widget-aware replacements for low-level `wevra.web`
layout defaults, but those replacements are selected only through existing
module ordering.

Alternative considered: adding a widget-specific layout injection or override
layer. That would create another precedence system and make template behaviour
harder to reason about. Existing module ordering is sufficient and already
matches the Wevra composition model.

### Represent widgets as optional features inside the module

The module should expose a small internal feature registry or equivalent
declaration shape. Each feature can declare the resources it contributes:
templates, partials, routes, context providers, and static assets. Configuration
then selects which features are active.

Alternative considered: one submodule per widget with separate module-list
entries. That would make simple UX defaults noisy to configure and would make
common layout coordination harder. A single `wevra.widgets` module with
feature-level configuration keeps the site module list readable while still
allowing granular behaviour.

### Keep feature dependencies capability-based

Widget features that need data from auth, database, or application behaviour
should obtain it through public Site capabilities or context providers. The
widgets module should not import provider internals or assume a specific module
implementation.

Alternative considered: direct imports from modules such as `wevra.auth`. That
would make widgets tightly coupled to specific providers and would undermine the
replaceable capability model.

### Move the theme selector as the first concrete feature

The existing theme mode selector becomes the initial implemented widget feature.
Its templates, routes, context, and assets move under `wevra.widgets`, while the
semantic theme-token foundation remains owned by `wevra.web` and the application
stylesheet layer.

Alternative considered: leaving the selector in `wevra.web`. That keeps the
current implementation smaller, but it blurs the boundary between rendering
foundation and optional UI components.

### Make widget layouts overridable partial compositions

Widget-aware layout templates should include feature partials rather than
embedding all behaviour directly in a monolithic template. This keeps individual
features replaceable and allows applications to override either the whole layout
or only a specific partial.

Alternative considered: each feature mutates or injects itself into arbitrary
layouts. That would be difficult to validate, order, and override. Template
partials give the same practical result with clearer ownership.

## Risks / Trade-offs

- Widget-aware layouts may surprise developers if module order is wrong →
  document expected ordering and rely on existing template precedence.
- Feature-level configuration may grow inconsistent as more widgets are added →
  keep the first configuration shape small and require later widgets to follow
  the same pattern.
- Moving the theme selector may temporarily expose unclear ownership between
  `wevra.web`, the app, and `wevra.widgets` → keep semantic tokens in the web
  foundation and move only selector UI behaviour into widgets.
- Widget routes can collide with application or other module routes → use
  existing route publication and first-module-wins duplicate handling.
- Optional features that depend on absent capabilities could fail at startup or
  render time → require feature implementations to degrade clearly or fail with
  explicit configuration errors when a required capability is enabled but absent.
