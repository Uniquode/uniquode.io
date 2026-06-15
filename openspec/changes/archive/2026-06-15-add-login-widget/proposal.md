## Why

Wevra widgets should provide common authentication entry points out of the box so host applications do not repeat login/logout header boilerplate. The next widget should make authenticated state visible in the shared layout while remaining optional, overridable, and composed through the existing widgets module.

## What Changes

- Add a `login` widget feature to `wevra.widgets` that is enabled by default when auth is available.
- Render a login button when no current user is resolved.
- Render a default profile avatar and logout button when a current user is resolved.
- Place the login/logout widget in the header action area, flush right and immediately to the left of the existing theme selector when both are enabled.
- Collapse the profile avatar on mobile layouts so the login/logout action remains centred within its compact control area.
- Use auth route names for links: `auth:login` for login and `auth:logout` for logout.
- Use an auth-owned helper to provide the default profile image for now; auth may generate an SVG from the capitalised first email character until profile support moves that responsibility into a profile module.
- Keep the widget optional and controlled through `wevra.widgets` feature configuration, while defaulting it on when the composed site provides auth.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-widgets`: add the authentication login/logout widget feature, including configured enablement, auth-state rendering, header placement, mobile behaviour, and default avatar behaviour.

## Impact

- Affects `wevra.widgets` feature configuration, templates, context use, and static styling. Feature options should use TOML-friendly per-feature configuration sections rather than forcing all future options into a flat feature list.
- Depends on public auth/session context or capability access when auth is available; if auth is absent, the default login widget is not rendered.
- Requires tests or validation covering logged-out rendering, logged-in rendering, feature disablement, header ordering, and mobile avatar collapse semantics.
- Does not require host applications to add custom routes or layout code to get the default login/logout control.
