# 0003: CSS Strategy and Theming Conventions

Date: 2026-05-20

Status: Provisional

## Context

The project is now close to defining its initial template hierarchy and front-end conventions.

ADR 0004 established a server-rendered web foundation using Jinja2, with `htmx` as the preferred dynamic enhancement layer where needed. That decision still leaves open how the project should approach baseline styling, responsive layout, reusable widgets, and colour-mode support.

Building all CSS from scratch would maximise control, but it would also require the project to define and maintain consistent defaults for typography, forms, tables, navigation, layout, spacing, visual states, and reusable interface elements from the beginning.

The project wants:

- responsive default behaviour;
- a styling baseline that works well with server-rendered templates;
- a path to reusable widgets and interface consistency;
- support for `auto`, `light`, and `dark` display modes;
- a lighter dependency and build surface than a large front-end framework.

Heavier class-oriented frameworks such as Bulma remain viable, but they would impose a stronger component and markup model earlier than the project currently needs.

## Decision

Use Pico CSS as the baseline CSS framework for the project.

Use Pico to provide the default responsive, semantic HTML-friendly styling foundation for templates, forms, tables, navigation, and general layout.

Layer a small amount of project-specific CSS on top of Pico for branding, design tokens, reusable widgets, and application-specific adjustments.

Support `auto`, `light`, and `dark` theme modes as a project requirement.

Treat theme support primarily as a token and theming concern rather than as a reason to introduce a heavier CSS framework.

Keep reusable UI building blocks primarily in template partials, macros, or related server-rendered composition patterns, with CSS supporting those building blocks rather than defining a separate front-end component system.

Avoid introducing a heavier CSS framework unless future UI complexity clearly justifies the added weight, stronger framework conventions, or a richer styling build pipeline.

## Consequences

The project gets a responsive and coherent styling baseline quickly, without needing to design every primitive from scratch before the first usable pages exist.

Server-rendered templates can remain relatively clean because Pico works well with semantic HTML and does not require an aggressively utility-driven markup style.

The project still retains room for custom visual direction through a thin project-specific CSS layer.

Supporting multiple theme modes from the start reduces the risk of retrofitting theme tokens later across many templates and widgets.

Pico may not cover every future component pattern out of the box. If the interface grows substantially more complex, the project may need to expand its custom CSS layer or revisit the framework choice in a later ADR.

## Open Questions

- Whether Pico should be consumed as a vendored static asset, an installed package, or another managed dependency form.
- Whether the initial implementation should use Pico's defaults almost unchanged or immediately introduce project-level design tokens and overrides.
- Where the user's theme preference should be stored when overriding `auto`, such as a cookie, session value, database preference, or browser-local storage.
- Whether any additional styling or asset build step is needed beyond baseline CSS delivery.
- What naming convention should be used for project-specific widget or component classes layered on top of Pico.

## Follow-Up Work

- Define how Pico is included in the application.
- Define the base stylesheet structure and project override conventions.
- Define the initial theme-mode behaviour for `auto`, `light`, and `dark`.
- Define template and widget conventions that align with the Pico baseline.
