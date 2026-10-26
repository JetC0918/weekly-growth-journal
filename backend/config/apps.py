from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.config"

    def ready(self):
        from . import checks  # noqa: F401
        from .telemetry import configure_telemetry

        configure_telemetry()
