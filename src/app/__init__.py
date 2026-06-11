from wevra.config import ConfigDef, ConfigSection

__version__ = "0.1.0"

module_config = ConfigDef(
    {
        "app": ConfigSection(
            fields={
                "alembic_config",
                "app_name",
                "csrf_cookie_secure",
                "csrf_token_secret",
                "database_url",
                "deployment_environment",
                "migrations_root",
            },
            defaults={
                "app_name": "uniquode",
                "database_url": "sqlite+aiosqlite:///app.sqlite3",
                "deployment_environment": "local",
            },
            env={
                "alembic_config": "ALEMBIC_CONFIG",
                "app_name": "APP_NAME",
                "csrf_cookie_secure": "CSRF_SECURE",
                "csrf_token_secret": "CSRF_SECRET",
                "database_url": "DATABASE_URL",
                "deployment_environment": "APP_ENV",
                "migrations_root": "MIGRATIONS_ROOT",
            },
        ),
        "app.static": ConfigSection(
            fields={"root", "url_path"},
            defaults={"url_path": "/static/"},
            env={
                "root": "STATIC_ROOT",
                "url_path": "STATIC_URL",
            },
        ),
        "app.templates": ConfigSection(
            fields={"auto_reload", "cache_size", "root"},
            env={"root": "TEMPLATE_ROOT"},
        ),
    }
)

__all__ = ("__version__", "module_config")
