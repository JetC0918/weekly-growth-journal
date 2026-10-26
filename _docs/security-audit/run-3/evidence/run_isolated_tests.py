"""Run real Django suites on synthetic SQLite memory data, never the configured DB.

This verifies request/model behavior; it does not establish PostgreSQL locking,
TLS, Hyperdrive compatibility or deployed behavior.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
os.environ["DJANGO_SETTINGS_MODULE"] = "backend.config.settings"
os.environ["APP_ENV"] = "development"
os.environ["DJANGO_DEBUG"] = "true"
os.environ["AI_PROVIDER_MODE"] = "openai"
os.environ["AI_API_KEY"] = ""
os.environ["OTEL_SDK_DISABLED"] = "true"

from django.conf import settings

settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

import django
from django.test.utils import get_runner

django.setup()
runner = get_runner(settings)(verbosity=2, interactive=False)
# The remaining journey explicitly requires PostgreSQL in its setUp; SQLite
# cannot verify its backend-specific contract. Existing provider tests inject
# their own synthetic transports/settings and never require a live API key.
raise SystemExit(bool(runner.run_tests([
    "backend.accounts",
    "backend.config",
    "backend.feedback",
    "backend.journal.tests.JournalAPITests",
])))
