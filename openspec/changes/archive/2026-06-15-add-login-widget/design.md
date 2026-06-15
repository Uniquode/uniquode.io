## Context

`wevra.widgets` now owns optional UI support features that can override the baseline web layout through normal module ordering. The theme selector is the first widget feature; the login/logout control should follow the same pattern so authentication entry points are available without host-app layout boilerplate.

Authentication state is already a composed concern: when `wevra.auth` is active it contributes request/user context and named routes. The login widget should consume that public surface rather than importing auth internals or requiring host applications to wire buttons manually.

## Goals / Non-Goals

**Goals:**

- Add a `login` widget feature controlled by `wevra.widgets` feature configuration and enabled by default when auth is available.
- Render anonymous and authenticated states through overridable widget partials.
- Keep the header action order deterministic: login/logout immediately left of the theme selector.
- Keep mobile behaviour explicit: hide the avatar and centre the login/logout action in compact layouts.
- Use an auth-owned profile image descriptor for the temporary avatar, initially carrying fallback text generated from the authenticated user's email initial.
- Treat auth availability as the default enablement condition, and avoid rendering the login widget when auth routes are unavailable.

**Non-Goals:**

- Build profile management or uploaded profile pictures.
- Add new auth routes or change the auth session model.
- Require applications to include custom login/logout templates to use the default widget.
- Add compatibility shims for older widget template contracts.
- Build a generic profile module; avatar generation can move there later.

## Decisions

### The login control is a `wevra.widgets` feature

The feature will use the same feature configuration mechanism as the theme selector, but its default enabled state is conditional on auth availability. This keeps optional UI concerns in the widgets module and avoids making `wevra.web` aware of authentication UI.

Alternative considered: place the control in `wevra.auth`. That would make auth own layout integration, but it would also force auth to understand widget ordering and header composition. Keeping the control in `wevra.widgets` preserves the role of widgets as the UI composition layer.

### Templates use a stable header action partial

The widget-aware layout should expose a header actions area that includes enabled widget partials in deterministic order. The login partial appears before the theme partial so it renders flush right and immediately to the left of the theme button when both exist.

Alternative considered: let each feature inject itself independently into the layout. That would make ordering implicit and fragile. A single header action composition partial makes ordering explicit and overridable.

### Auth state is sourced from public request context or capability access

The login widget should derive the current user from the request context populated by auth, or another public capability-backed helper if that is the established API at implementation time. It must not import private auth session machinery directly.

If auth is available and no authenticated user is resolved, the widget renders the anonymous login state. If auth is absent, the widget does not render by default. Explicit configuration can still disable the feature.

Alternative considered: the login partial could call auth functions directly. That would couple widget rendering to auth implementation details and make replacement auth modules harder.

### Default avatar is deterministic and data-light

Until profile images exist, `wevra.auth` should expose a public profile image descriptor for the login widget to obtain display data. The descriptor should support an image source when available and fallback text when no image exists. For now auth can provide fallback text from the first character of the user's email address, capitalised. This keeps identity-display logic with auth for now and leaves a clean seam for moving it to a future profile module, uploaded profile images, or Gravatar.

Alternative considered: generate SVG directly in `wevra.widgets`. That would make the temporary implementation look like the durable API. A descriptor keeps the widget able to render uploaded images, Gravatar, or fallback text without changing the widget contract.

### Responsive behaviour is CSS-owned

The login/logout partial should render both desktop elements and semantic classes. CSS hides the avatar in mobile layouts and centres the login/logout button in its compact control area. Breakpoints and reusable responsive support should come from `wevra.web`, with `wevra.widgets` consuming those conventions rather than defining unrelated media-query policy. This avoids branching server templates on viewport size.

Alternative considered: render different markup server-side for mobile. The server does not reliably know viewport width, so CSS is the correct layer.

## Risks / Trade-offs

- Auth route names may not exist when auth is absent or replaced → use auth-route availability as the default enablement signal and do not render the login widget when those routes are unavailable.
- Feature configuration may need options soon → preserve the existing simple feature enablement while favouring TOML-friendly per-feature config tables for new options rather than overloading a flat feature list.
- Request context shape may change while the auth capability API is still forming → keep the widget implementation isolated behind a small helper that extracts the template user state.
- Header layout overrides may accidentally remove widget controls → this is acceptable under normal template precedence; applications that override the header own that markup.
- Avatar generated from email exposes the email initial → this is acceptable for the default authenticated UI, and full profile-display policy can be revisited with profile support.
