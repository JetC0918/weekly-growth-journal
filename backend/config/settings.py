"""Django configuration for local development and the backend foundation."""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parents[2]
APP_ENV = os.environ.get("APP_ENV", "development").strip().lower()
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-development-key-change-before-deploy")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS_EXPLICIT = "DJANGO_ALLOWED_HOSTS" in os.environ
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
    if host.strip()
]
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "backend.config.apps.ConfigConfig",
    "backend.accounts.apps.AccountsConfig",
    "backend.journal.apps.JournalConfig",
    "backend.feedback.apps.FeedbackConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
CORS_ALLOW_HEADERS = ("authorization", "content-type")

ROOT_URLCONF = "backend.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.config.wsgi.application"
ASGI_APPLICATION = "backend.config.asgi.application"


def _database_config():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("DATABASE_URL must use the postgres or postgresql scheme")
        options = {}
        sslmode = parse_qs(parsed.query).get("sslmode", [None])[-1]
        if not sslmode and APP_ENV == "production":
            # Render's internal Postgres URL omits sslmode, but supports TLS.
            sslmode = "require"
        if sslmode:
            options["sslmode"] = sslmode
        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": 60,
        }
        if options:
            config["OPTIONS"] = options
        return config

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "weekly_growth_journal"),
        "USER": os.environ.get("POSTGRES_USER", "weekly_growth_journal"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "weekly-growth-local"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5433"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": os.environ["POSTGRES_SSLMODE"]}
        if os.environ.get("POSTGRES_SSLMODE")
        else {},
    }


DATABASE_CONFIG_EXPLICIT = bool(os.environ.get("DATABASE_URL")) or all(
    os.environ.get(name)
    for name in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST")
)
DATABASES = {"default": _database_config()}
TOKEN_SIGNING_KEY = os.environ.get("TOKEN_SIGNING_KEY", "local-development-token-key-change-before-deploy")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").strip()
AI_MODEL = os.environ.get("AI_MODEL", "gpt-4o-mini").strip()
AI_API_KEY = os.environ.get("AI_API_KEY", "").strip()
AI_PROVIDER_MODE = os.environ.get("AI_PROVIDER_MODE", "openai").strip().lower()

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.accounts.authentication.SignedBearerAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "backend.accounts.exceptions.openapi_exception_handler",
}
