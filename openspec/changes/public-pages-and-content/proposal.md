## Why

Linear: [UT-175](https://linear.app/uniquode/issue/UT-175/public-pages-and-content)

The web foundation has established server-rendered page conventions, template
resources, and route-surface behaviour, but public-facing content is still
minimal. This change defines the public pages and content slice so the
application has clear conventions for public page delivery and a deliberate
decision about whether content needs domain-owned records with slugs.

## What Changes

- Introduce public page conventions for application-owned public routes and
  templates.
- Decide whether public content requires content-managed records, static
  templates, or another lightweight representation.
- Keep content slugs in the domain/content layer rather than hard-coding content
  identity into route registration.
- Define how public pages participate in the existing template, theme, route,
  validation, and error-handling surfaces.
- Preserve a small implementation surface until concrete product content
  requirements justify a richer content model.

## Capabilities

### New Capabilities

- `public-content`: Public page/content modelling, slug policy, rendering
  conventions, and validation expectations.

### Modified Capabilities

- `html-ui-foundation`: Extend page conventions for public-facing content and
  template usage.
- `module-web-composition`: Ensure public page modules can publish routes and
  template resources consistently when that composition change is implemented.

## Impact

- Affected areas include public routes, templates, content/domain modelling,
  route validation, README/operator documentation, and future navigation
  structure.
- This proposal should avoid introducing a CMS, editor, asset pipeline, or
  persistence model until the spec/design confirms a requirement.
- Existing public home-page behaviour should remain compatible while the public
  content conventions are formalised.
