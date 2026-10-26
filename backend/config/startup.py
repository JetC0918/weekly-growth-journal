"""Startup guards shared by Django entry points and platform adapters."""

from collections.abc import Callable
from typing import TypeVar

from django.conf import settings
from django.core.checks import ERROR, run_checks
from django.core.management.base import SystemCheckError

_Application = TypeVar("_Application")


def get_checked_application(application_factory: Callable[[], _Application]) -> _Application:
    """Build the Django app and block serving when deployment checks fail.

    Django registers deployment checks during setup, which the application
    factory performs. Development keeps its local defaults; every other
    environment must pass the deployment checks before the app is returned.
    """
    application = application_factory()
    if settings.APP_ENV == "development":
        return application

    errors = [
        message
        for message in run_checks(include_deployment_checks=True)
        if message.level >= ERROR
    ]
    if errors:
        raise SystemCheckError(errors)
    return application
