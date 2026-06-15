## 1. Module Structure

- [x] 1.1 Create the `wevra.widgets` package with module exports compatible with Wevra site composition.
- [x] 1.2 Add widget module resource declarations for package templates and static assets.
- [x] 1.3 Add widget module route declarations for widget-owned dynamic routes.
- [x] 1.4 Add widget module context-provider registration for enabled widget features.

## 2. Widget Feature Configuration

- [x] 2.1 Define the `wevra.widgets` configuration shape for enabled and disabled features.
- [x] 2.2 Implement feature configuration loading through the existing Wevra configuration service.
- [x] 2.3 Reject unknown widget feature names with an explicit configuration error.
- [x] 2.4 Ensure disabled features do not publish routes, context providers, or default rendered partials.

## 3. Widget Feature Infrastructure

- [x] 3.1 Define the internal widget feature declaration shape for templates, partials, routes, context providers, and static assets.
- [x] 3.2 Compose enabled widget features into the module surface during `wevra.widgets` setup.
- [x] 3.3 Ensure widget feature dependencies use public Site capabilities or request context rather than provider internals.
- [x] 3.4 Ensure optional missing dependencies degrade cleanly and required missing dependencies fail explicitly.

## 4. Theme Selector Migration

- [x] 4.1 Locate the existing `auto`/`light`/`dark` selector templates, routes, context providers, and assets.
- [x] 4.2 Move selector UI behaviour into a `wevra.widgets` theme selector feature.
- [x] 4.3 Keep semantic theme token definitions owned by `wevra.web` and the application stylesheet layer.
- [x] 4.4 Ensure the selector renders only when the theme selector feature is enabled.
- [x] 4.5 Ensure selector update requests are handled by widget-owned routes or equivalent widget-owned handlers.

## 5. Layouts And Partials

- [x] 5.1 Add widget-aware default layout templates that can supersede `wevra.web` defaults through normal module ordering.
- [x] 5.2 Render enabled widget features through overridable partial templates.
- [x] 5.3 Ensure application-provided templates and partials can override widget templates through existing resource precedence.
- [x] 5.4 Avoid any special layout injection or hidden page mutation mechanism.

## 6. Application Composition

- [x] 6.1 Update default or example site configuration to include `wevra.widgets` in the intended module order.
- [x] 6.2 Configure the initial theme selector feature through `wevra.widgets` configuration.
- [x] 6.3 Remove application-owned or `wevra.web`-owned theme selector wiring that now belongs to `wevra.widgets`.
- [x] 6.4 Leave login/user/logout and site navigation widgets unimplemented for follow-up changes.

## 7. Validation And Tests

- [x] 7.1 Add tests for widget feature configuration, including enabled, disabled, and unknown feature cases.
- [x] 7.2 Add tests for widget module resource and route publication through normal module composition.
- [x] 7.3 Add tests proving application templates can override widget layouts and partials.
- [x] 7.4 Add tests proving the theme selector is available when enabled and absent when disabled.
- [x] 7.5 Add or update validation checks for widget feature configuration and published widget resources.
