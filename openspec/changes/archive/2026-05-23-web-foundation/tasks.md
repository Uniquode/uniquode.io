## 1. Source Layout and Configuration

- [x] 1.1 Create the default `src/templates/` and `src/static/` roots and add the initial layout, error, and component directories needed by the web foundation.
- [x] 1.2 Update the project settings and app factory so the template root, static root, and static route prefix are configurable, with defaults wired into the running application and static asset mounting.
- [x] 1.3 Introduce the baseline declarative route-registration structure needed to keep page, partial, and future API surfaces distinct, starting with the `site` module pattern.

## 2. Rendering and Route Foundation

- [x] 2.1 Implement the initial rendering helper that renders templates from the configured template root and supports consistent page and error rendering.
 - [x] 2.2 Implement the initial HTML dispatcher protocol and declarative view registry for page-oriented views under FastAPI.
 - [x] 2.3 Add the first base templates, shared component examples, and a small baseline `site` page or pages that exercise the dispatcher and rendering conventions.
- [x] 2.4 Add stable route naming or identifiers for the implemented web routes and document the reverse-resolution expectations in code or adjacent project docs where needed.

## 3. Styling and Dynamic Enhancement Baseline

- [x] 3.1 Add the MVP Pico CSS integration using the chosen lightweight delivery approach and layer project-specific stylesheet entry points separately.
- [x] 3.2 Add the baseline `htmx` delivery and at least one partial-rendering flow that proves the page-versus-partial boundary.
- [x] 3.3 Add separate development-time static asset serving using the configured static route prefix and keep the contract compatible with future production offload.
- [x] 3.4 Implement the initial theme-mode handling required for `auto`, `light`, and `dark` behaviour in the web foundation slice.
- [x] 3.5 Replace hard-coded light-mode visual assumptions with semantic theme tokens and apply those tokens across the shared templates and project stylesheet layer.
- [x] 3.6 Update the theme-mode interaction so changing theme preference updates the live page shell immediately, not only after a full page reload.
- [x] 3.7 Replace the form-style theme selector with a reusable icon-based component that updates immediately and can be embedded into relevant pages.

## 4. Validation and Verification

- [x] 4.1 Implement the first web-structure validation command or CLI surface for the currently supported dispatcher, route, template, and static asset structures.
- [x] 4.2 Add focused tests for dispatcher selection, declarative route/view registration, template rendering, static asset wiring, route-surface separation, and the implemented validation behaviour.
- [x] 4.3 Run the relevant project validation commands and update documentation or local guidance needed to describe the new web foundation workflow.
- [x] 4.4 Add focused verification that `auto`, `light`, and `dark` theme modes produce semantic styling changes through shared tokens rather than template-specific colour branching.
- [x] 4.5 Add focused verification that the theme-mode interaction updates the document theme state through the live `htmx` flow.
- [x] 4.6 Add focused verification that the reusable theme-selector component renders the current-mode icon and cycles mode through the live partial flow.
