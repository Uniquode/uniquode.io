REQUIRED_STATIC_ASSETS: tuple[str, ...] = ("styles/app.css",)

REQUIRED_THEME_TOKENS: tuple[str, ...] = (
    "--u-colour-page-bg",
    "--u-colour-surface",
    "--u-colour-text",
    "--u-colour-muted-text",
    "--u-colour-border",
    "--u-colour-accent",
)

REQUIRED_THEME_SELECTORS: tuple[str, ...] = (
    'html[data-theme="light"]',
    'html[data-theme="dark"]',
    "@media (prefers-color-scheme: dark)",
)
