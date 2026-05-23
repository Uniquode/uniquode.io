# uniquode.io Design

## Status

This document records the current design baseline used in the repository.
It is intentionally provisional and should be revised once the project has
more real screens, workflows, and examples in use.

It describes what the project is doing now. It is not a licence to introduce
new visual systems, front-end tooling, or branding directions without an
explicit decision.

## Purpose

The current design direction is meant to:

- provide a clean server-rendered baseline that works well with semantic HTML;
- keep styling simple while the product surface is still small;
- support `auto`, `light`, and `dark` theme modes from the start;
- leave room for a clearer branded visual language once more of the site exists;
- avoid introducing a front-end build pipeline before there is a real need.

## Current Foundation

### Delivery model

- The UI is server-rendered first.
- Jinja2 templates are the primary rendering mechanism for pages and partials.
- `htmx` is the preferred progressive-enhancement layer for partial updates.
- Baseline interactions must still work as ordinary HTML without depending on
  `htmx`.

### Styling baseline

- Pico CSS is the current baseline CSS framework.
- Pico is delivered by CDN rather than a local asset pipeline.
- Project-specific CSS is layered separately in `src/static/styles/app.css`.
- The project should continue to prefer semantic HTML over dense utility-class
  markup.

### Asset and template structure

- Global templates live under `src/templates/`.
- Global static assets live under `src/static/`.
- Shared template components live under `src/templates/components/`.
- Feature-specific templates should live under conventional subpaths such as
  `src/templates/public/`.

## Visual Direction

The current visual direction is deliberately light and restrained:

- soft, pale backgrounds rather than stark white;
- a single blue-led accent used for emphasis;
- broad spacing and simple page structure;
- minimal ornament beyond a soft radial highlight and gentle background
  gradient;
- typography and most base element styling inherited from Pico.

This should be treated as a starting point, not as final brand expression.

## Current Tokens And Rules

### Colour

Current project CSS defines:

- light accent: `#4b5c92`
- dark accent: `#b4c5ff`
- accent-soft: derived from the accent with `color-mix(...)`

Current page backgrounds use:

- a radial highlight in the accent-soft colour;
- a vertical background gradient:
  - light: `#faf8ff` to `#f4f3fa`
  - dark: `#121318` to `#1a1b21`

Guidance:

- keep the palette narrow until stronger branding requirements exist;
- add named project tokens before adding many one-off colours;
- prefer extending the token layer rather than scattering literal colour
  values through templates or component CSS.

### Theme modes

- Supported modes are `auto`, `light`, and `dark`.
- `auto` is the default behaviour.
- Explicit user selection is currently persisted in a cookie.
- The page root may set `data-theme` for non-`auto` modes.

Guidance:

- theme behaviour should remain token-driven;
- future component work should inherit from the active theme rather than
  hard-coding light-only assumptions.

### Layout

Current page-level rules include:

- a main content container capped at `56rem`;
- generous vertical padding on the main container;
- simple stacked sections and content blocks;
- no complex responsive layout system yet beyond what Pico already provides.

Guidance:

- prefer simple document flow before introducing bespoke layout primitives;
- add layout utilities only when repeated page patterns justify them.

### Typography

- No custom project font has been adopted yet.
- Typography currently follows the Pico baseline.
- Eyebrow text is styled as small uppercase accent text with increased letter
  spacing and heavier weight.

Guidance:

- do not introduce a custom type pairing until there is enough real UI to
  evaluate it properly;
- when typography is expanded, document primary, secondary, and monospace roles
  explicitly.

## Component Direction

- Reusable UI building blocks should be expressed through Jinja components,
  includes, partials, and macros.
- CSS should support those building blocks rather than creating a separate
  component runtime.
- Prefer shared components only when reuse is real; otherwise keep markup local
  to the feature area.

The current baseline includes:

- a shared theme-switcher component;
- a public feature partial for theme status;
- a base page layout used by the public home page.

## Interaction Direction

- `htmx` should be used where partial updates genuinely improve the experience.
- Partial routes should return fragments only, not full-page shells.
- Full-page routes, partial routes, and API routes must stay distinct.
- Dynamic behaviour should remain understandable from HTML templates and route
  definitions without requiring a client-side application architecture.

## What Is Intentionally Not Decided Yet

The following are still open and should not be treated as settled by this
document alone:

- final brand palette;
- final typography system;
- icon system beyond what the Design MCP can help evaluate later;
- illustration, photography, or marketing art direction;
- animation and motion language;
- whether Pico remains sufficient once the interface grows;
- whether any front-end build tooling is justified later.

## Working Rules For Future Revisions

- Update this document when a design decision is actually adopted in code or
  explicitly accepted as a project direction.
- Prefer evolving this file from real examples rather than inventing a complete
  visual system in advance.
- Keep it aligned with ADR 0003 and ADR 0004 until those decisions are revised.
- Use the repository Stitch project `uniquode.io` for future design-system and
  `DESIGN.md` workflows.
