import os

from django.core.asgi import get_asgi_application

from .startup import get_checked_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

application = get_checked_application(get_asgi_application)
