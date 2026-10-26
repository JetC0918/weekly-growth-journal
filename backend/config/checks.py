"""Fail-closed deployment checks for production configuration."""

import os
from ipaddress import ip_address
from urllib.parse import urlsplit

from django.conf import settings
from django.core.checks import Error, register

_DEVELOPMENT_DJANGO_KEY = "local-development-key-change-before-deploy"
_DEVELOPMENT_TOKEN_KEY = "local-development-token-key-change-before-deploy"


def _invalid_production_origin(origin):
    """Return whether a CORS entry is not one exact HTTPS origin URL."""
    if not isinstance(origin, str) or not origin or origin != origin.strip() or "*" in origin:
        return True
    try:
        parsed = urlsplit(origin)
        port = parsed.port
    except ValueError:
        return True
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
        or any(char.isspace() for char in origin)
        or "?" in origin
        or "#" in origin
    ):
        return True
    hostname = parsed.hostname
    if ":" in hostname:
        try:
            if ip_address(hostname).version != 6:
                return True
        except ValueError:
            return True
    else:
        labels = hostname.split(".")
        if any(
            not label
            or len(label) > 63
            or not label[0].isalnum()
            or not label[-1].isalnum()
            or not all(char.isalnum() or char == "-" for char in label)
            for label in labels
        ):
            return True
        if len(hostname) > 253:
            return True
    if port is not None and not 1 <= port <= 65535:
        return True
    return False


@register(deploy=True)
def check_production_configuration(app_configs, **kwargs):
    errors = []
    if settings.APP_ENV not in {"development", "production"}:
        return [
            Error(
                "APP_ENV must be set to either development or production.",
                id="config.E001",
            )
        ]
    if settings.APP_ENV != "production":
        return errors

    if settings.AI_PROVIDER_MODE not in {"openai", "fake"}:
        errors.append(Error("AI_PROVIDER_MODE must be openai or fake.", id="config.E014"))
    elif settings.AI_PROVIDER_MODE == "fake" and not settings.DEBUG:
        errors.append(Error("The fake AI provider is available only when DEBUG is true.", id="config.E015"))

    if settings.DEBUG:
        errors.append(Error("DJANGO_DEBUG must be false in production.", id="config.E002"))

    # LazySettings.SECRET_KEY raises ImproperlyConfigured on an empty value,
    # while deployment checks need to report that state as a normal check error.
    django_key = getattr(settings._wrapped, "SECRET_KEY", "")
    token_key = settings.TOKEN_SIGNING_KEY
    if not django_key.strip() or django_key == _DEVELOPMENT_DJANGO_KEY:
        errors.append(Error("DJANGO_SECRET_KEY must be set to a production secret.", id="config.E003"))
    if not token_key.strip() or token_key == _DEVELOPMENT_TOKEN_KEY:
        errors.append(Error("TOKEN_SIGNING_KEY must be set to a production secret.", id="config.E004"))
    if django_key and token_key and django_key == token_key:
        errors.append(Error("Django and token signing keys must be different.", id="config.E005"))

    if not settings.DATABASE_CONFIG_EXPLICIT:
        errors.append(Error("Configure a PostgreSQL connection for production.", id="config.E006"))
    database = settings.DATABASES.get("default", {})
    if database.get("ENGINE") != "django.db.backends.postgresql":
        errors.append(Error("The production database must use PostgreSQL.", id="config.E007"))
    for field in ("NAME", "USER", "PASSWORD", "HOST"):
        if not str(database.get(field, "")).strip():
            errors.append(Error("The production PostgreSQL connection is incomplete.", id="config.E008"))
    sslmode = database.get("OPTIONS", {}).get("sslmode", "")
    connection_kind = getattr(
        settings,
        "DATABASE_CONNECTION_KIND",
        os.environ.get("DATABASE_CONNECTION_KIND", "postgresql"),
    )
    if connection_kind == "cloudflare-hyperdrive":
        if sslmode != "disable":
            errors.append(
                Error(
                    "The Worker-to-Hyperdrive socket must disable TLS; Hyperdrive must require TLS to the PostgreSQL origin.",
                    id="config.E011",
                )
            )
    elif sslmode not in {"require", "verify-ca", "verify-full"}:
        errors.append(Error("The production PostgreSQL connection must require TLS.", id="config.E011"))

    if not settings.ALLOWED_HOSTS_EXPLICIT or not settings.ALLOWED_HOSTS:
        errors.append(Error("Set an explicit DJANGO_ALLOWED_HOSTS production allowlist.", id="config.E009"))
    elif "*" in settings.ALLOWED_HOSTS:
        errors.append(Error("DJANGO_ALLOWED_HOSTS must not contain a wildcard.", id="config.E010"))

    cors_origins = settings.CORS_ALLOWED_ORIGINS
    if not cors_origins:
        errors.append(Error("Set an explicit HTTPS CORS_ALLOWED_ORIGINS allowlist.", id="config.E012"))
    elif any(_invalid_production_origin(origin) for origin in cors_origins):
        errors.append(
            Error(
                "CORS_ALLOWED_ORIGINS must contain only exact HTTPS origins without paths or wildcards.",
                id="config.E013",
            )
        )

    return errors
