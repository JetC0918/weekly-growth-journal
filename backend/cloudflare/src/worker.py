"""Cloudflare Python Worker adapter for the Django WSGI application.

The production bindings are copied into the process environment before Django
loads settings. Hyperdrive terminates the upstream database connection; its
Python Workers example uses a non-TLS socket from the Worker to Hyperdrive.
"""

from __future__ import annotations

import os
import threading
from urllib.parse import quote

from workers import WorkerEntrypoint, wsgi

_application = None
_application_lock = threading.Lock()


def _set_required_environment(env) -> None:
    required = (
        "DJANGO_SECRET_KEY",
        "TOKEN_SIGNING_KEY",
        "DJANGO_ALLOWED_HOSTS",
        "CORS_ALLOWED_ORIGINS",
    )
    missing = [name for name in required if not getattr(env, name, "")]
    if missing:
        raise RuntimeError("Missing required Worker bindings: " + ", ".join(missing))

    hyperdrive = env.HYPERDRIVE
    database_url = "postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=disable".format(
        user=quote(hyperdrive.user, safe=""),
        password=quote(hyperdrive.password, safe=""),
        host=hyperdrive.host,
        port=hyperdrive.port,
        database=quote(hyperdrive.database, safe=""),
    )

    os.environ.update(
        {
            "DJANGO_SETTINGS_MODULE": "backend.config.settings",
            "APP_ENV": "production",
            "DJANGO_DEBUG": "false",
            "DATABASE_CONNECTION_KIND": "cloudflare-hyperdrive",
            "DJANGO_SECRET_KEY": env.DJANGO_SECRET_KEY,
            "TOKEN_SIGNING_KEY": env.TOKEN_SIGNING_KEY,
            "DJANGO_ALLOWED_HOSTS": env.DJANGO_ALLOWED_HOSTS,
            "CORS_ALLOWED_ORIGINS": env.CORS_ALLOWED_ORIGINS,
            "DATABASE_URL": database_url,
            # Fake responses are rejected by the existing production system check.
            "AI_PROVIDER_MODE": "openai",
            "AI_API_KEY": getattr(env, "AI_API_KEY", ""),
        }
    )


def _get_application(env):
    global _application
    if _application is None:
        with _application_lock:
            if _application is None:
                _set_required_environment(env)
                from django.core.wsgi import get_wsgi_application
                from backend.config.startup import get_checked_application

                _application = get_checked_application(get_wsgi_application)
    return _application


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        application = _get_application(self.env)
        return await wsgi.fetch(application, request, self.env)
