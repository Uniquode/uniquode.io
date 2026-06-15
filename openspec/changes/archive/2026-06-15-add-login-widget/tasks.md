## 1. Widget Feature Configuration

- [x] 1.1 Add `login` as a recognised `wevra.widgets` feature.
- [x] 1.2 Ensure `login` can be enabled or disabled through the existing widgets feature configuration, preserving a path for TOML-friendly per-feature option sections.
- [x] 1.3 Enable `login` by default when auth is available, while allowing explicit feature configuration to disable it.

## 2. Auth State Integration

- [x] 2.1 Add a small widget-owned helper that resolves login-widget state from public request context or capability access.
- [x] 2.2 Represent anonymous state with a direct login link resolved from the route named `auth:login` when auth is available.
- [x] 2.3 Represent authenticated state with the current user, auth-provided profile image descriptor, and direct logout link resolved from the route named `auth:logout`.
- [x] 2.4 Avoid importing private auth session internals from `wevra.widgets`.

## 3. Templates And Layout

- [x] 3.1 Add an overridable login-widget partial for anonymous and authenticated states.
- [x] 3.2 Update the widget-aware header action composition so the login/logout control renders immediately to the left of the theme selector.
- [x] 3.3 Keep the login/logout control flush right with the rest of the header action group.
- [x] 3.4 Ensure application-provided templates can override the login partial or header action layout through normal template precedence.

## 4. Styling And Responsive Behaviour

- [x] 4.1 Add widget CSS for the login button, logout button, action group spacing, and default avatar.
- [x] 4.2 Add or use a public auth profile image descriptor that supports image sources and fallback text, with fallback text generated from the capitalised first email character for now.
- [x] 4.3 Use responsive support from `wevra.web` for mobile layout behaviour and hide the profile avatar in mobile layouts.
- [x] 4.4 Centre the login/logout action within its compact mobile control area.

## 5. Validation

- [x] 5.1 Extend widgets validation so an enabled login feature checks required templates and static assets.
- [x] 5.2 Ensure missing auth routes make the default login widget unavailable rather than causing startup failure.
- [x] 5.3 Report missing login-widget resources with actionable diagnostics.

## 6. Tests

- [x] 6.1 Test logged-out rendering shows a login button linked to `auth:login`.
- [x] 6.2 Test logged-in rendering shows avatar initial and logout button linked to `auth:logout`.
- [x] 6.3 Test disabling the login feature removes the login/logout control even when auth is available.
- [x] 6.4 Test header ordering places login/logout before the theme selector.
- [x] 6.5 Test mobile CSS semantics hide the avatar and preserve centred action styling.
- [x] 6.6 Test route/resource validation for the enabled login feature.

## 7. Root Application Integration

- [x] 7.1 Confirm the root application receives the login widget through default auth-aware widget enablement or explicit configuration if required.
- [x] 7.2 Remove any app-specific login/logout header boilerplate made redundant by the widget, if present.
