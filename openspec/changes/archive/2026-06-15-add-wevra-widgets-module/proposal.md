## Why

A Wevra web site is composed from ordered modules, but repeatable UI support
behaviour is still too easily pushed into the host application or low-level web
foundation. We need a dedicated `wevra.widgets` module that can provide sensible,
overridable UX defaults without making each application reimplement common
layout, partial, context, and `htmx` support.

## What Changes

- Add a new optional `wevra.widgets` module for reusable web UI support features.
- Treat widgets as normal module-composed web behaviour: ordering, template
  precedence, static resources, routes, and context providers use existing Wevra
  module composition rules.
- Position `wevra.widgets` as a module that is typically listed immediately
  after the application module so the application can provide first-priority
  overrides while widgets can still supersede low-level `wevra.web` defaults.
- Allow `wevra.widgets` to provide widget-aware default layouts and partials that
  override `wevra.web` templates through normal template resolution.
- Allow individual widget features to contribute:
  - overridable templates and partials
  - backend `htmx` routes for dynamic widget interactions
  - context providers for widget data sourced from configuration, database
    capabilities, or other module capabilities
  - static assets where needed
- Add configuration-driven feature enablement for `wevra.widgets`.
- Move the existing `auto`/`light`/`dark` theme mode selector into
  `wevra.widgets` as the first implemented widget feature.
- Leave additional widgets, such as login/user/logout controls and site
  navigation menus, to separate follow-up changes after the module and feature
  infrastructure exist.

## Capabilities

### New Capabilities

- `web-widgets`: Reusable, module-composed UI widget support for Wevra sites,
  including widget feature configuration, widget-aware layouts, overridable
  partials, dynamic widget routes, and widget context providers.

### Modified Capabilities

- `web-foundation`: Move the implemented theme mode selector out of the
  baseline web foundation and into `wevra.widgets`, while keeping semantic theme
  tokens and template/resource composition behaviour in the web foundation.

## Impact

- Affects Wevra web module composition, template resolution usage, context
  provider registration, route publication, and static resource publication.
- Adds a new public `wevra.widgets` module intended for inclusion in the
  configured module list.
- Moves theme selector templates, routes, context, and related assets from the
  current web/app location into `wevra.widgets`.
- Does not make auth, navigation, or other future widget behaviours part of this
  first implementation beyond defining the infrastructure needed to add them.
- Does not introduce a special override mechanism: widget layout and partial
  precedence must be achieved through existing Wevra module ordering.
