from django.core.checks import Error
from django.test import Client, SimpleTestCase, override_settings

from .checks import check_production_configuration


class ProductionConfigurationCheckTests(SimpleTestCase):
    valid_production_settings = {
        "APP_ENV": "production",
        "DEBUG": False,
        "SECRET_KEY": "unique-django-production-secret",
        "TOKEN_SIGNING_KEY": "unique-token-production-secret",
        "DATABASE_CONNECTION_KIND": "postgresql",
        "DATABASE_CONFIG_EXPLICIT": True,
        "DATABASES": {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "growth_journal",
                "USER": "growth_journal_app",
                "PASSWORD": "test-only-password",
                "HOST": "postgres.internal",
                "PORT": "5432",
                "OPTIONS": {"sslmode": "verify-full"},
            }
        },
        "ALLOWED_HOSTS_EXPLICIT": True,
        "ALLOWED_HOSTS": ["api.private.example"],
        "CORS_ALLOWED_ORIGINS": ["https://journal.private.example"],
    }

    def check(self, **overrides) -> list[Error]:
        settings = {**self.valid_production_settings, **overrides}
        with override_settings(**settings):
            return check_production_configuration(None)

    def test_complete_production_configuration_passes(self):
        self.assertEqual(self.check(), [])

    def test_development_mode_does_not_require_production_secrets_or_database(self):
        with override_settings(APP_ENV="development", SECRET_KEY="", TOKEN_SIGNING_KEY=""):
            self.assertEqual(check_production_configuration(None), [])

    def test_missing_or_development_signing_keys_fail_without_echoing_values(self):
        cases = (
            {"SECRET_KEY": ""},
            {"SECRET_KEY": "local-development-key-change-before-deploy"},
            {"TOKEN_SIGNING_KEY": ""},
            {"TOKEN_SIGNING_KEY": "local-development-token-key-change-before-deploy"},
            {"TOKEN_SIGNING_KEY": "unique-django-production-secret"},
        )
        for override in cases:
            with self.subTest(override=tuple(override)):
                errors = self.check(**override)
                self.assertTrue(errors)
                messages = " ".join(error.msg for error in errors)
                self.assertNotIn("unique-django-production-secret", messages)
                self.assertNotIn("unique-token-production-secret", messages)

    def test_debug_and_invalid_postgresql_configuration_fail(self):
        errors = self.check(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        )
        ids = {error.id for error in errors}
        self.assertIn("config.E002", ids)
        self.assertIn("config.E007", ids)
        self.assertIn("config.E008", ids)

    def test_missing_connection_and_host_allowlist_fail(self):
        errors = self.check(
            DATABASE_CONFIG_EXPLICIT=False,
            ALLOWED_HOSTS_EXPLICIT=False,
            ALLOWED_HOSTS=[],
        )
        ids = {error.id for error in errors}
        self.assertIn("config.E006", ids)
        self.assertIn("config.E009", ids)

    def test_wildcard_host_is_rejected(self):
        errors = self.check(ALLOWED_HOSTS=["*"])
        self.assertIn("config.E010", {error.id for error in errors})

    def test_postgresql_tls_is_required_in_production(self):
        database = self.valid_production_settings["DATABASES"]["default"].copy()
        database["OPTIONS"] = {}
        errors = self.check(DATABASES={"default": database})
        self.assertIn("config.E011", {error.id for error in errors})

    def test_postgresql_tls_disable_is_rejected_without_hyperdrive(self):
        database = self.valid_production_settings["DATABASES"]["default"].copy()
        database["OPTIONS"] = {"sslmode": "disable"}
        errors = self.check(DATABASES={"default": database})
        self.assertIn("config.E011", {error.id for error in errors})

    def test_hyperdrive_allows_non_tls_worker_socket_with_tls_origin_requirement(self):
        database = self.valid_production_settings["DATABASES"]["default"].copy()
        database["OPTIONS"] = {"sslmode": "disable"}
        self.assertEqual(
            self.check(
                DATABASE_CONNECTION_KIND="cloudflare-hyperdrive",
                DATABASES={"default": database},
            ),
            [],
        )

    def test_hyperdrive_requires_worker_socket_tls_to_be_disabled(self):
        database = self.valid_production_settings["DATABASES"]["default"].copy()
        database["OPTIONS"] = {"sslmode": "require"}
        errors = self.check(
            DATABASE_CONNECTION_KIND="cloudflare-hyperdrive",
            DATABASES={"default": database},
        )
        self.assertIn("config.E011", {error.id for error in errors})

    def test_unknown_environment_is_rejected(self):
        errors = self.check(APP_ENV="staging")
        self.assertEqual([error.id for error in errors], ["config.E001"])

    def test_missing_cors_allowlist_is_rejected_in_production(self):
        errors = self.check(CORS_ALLOWED_ORIGINS=[])
        self.assertIn("config.E012", {error.id for error in errors})

    def test_invalid_production_origins_are_rejected_without_echoing_values(self):
        invalid_origins = (
            "*",
            "https://*.private.example",
            "http://journal.private.example",
            "https://journal.private.example/path",
            "https://journal.private.example?query=1",
            "https://journal.private.example?",
            "https://journal.private.example#",
            "https://journal.private.example:bad",
            "https://user@journal.private.example",
            "https://journal..private.example",
            "https://-journal.private.example",
        )
        for origin in invalid_origins:
            with self.subTest(origin=origin):
                errors = self.check(CORS_ALLOWED_ORIGINS=[origin])
                self.assertIn("config.E013", {error.id for error in errors})
                self.assertNotIn(origin, " ".join(error.msg for error in errors))

    def test_explicit_https_origins_pass_production_check(self):
        self.assertEqual(
            self.check(CORS_ALLOWED_ORIGINS=[
                "https://journal.private.example",
                "https://journal-alt.private.example:8443",
            ]),
            [],
        )

    def test_production_rejects_fake_provider_mode(self):
        errors = self.check(AI_PROVIDER_MODE="fake")
        self.assertIn("config.E015", {error.id for error in errors})


class CorsHeaderTests(SimpleTestCase):
    allowed_origin = "https://journal.private.example"

    @override_settings(CORS_ALLOWED_ORIGINS=[allowed_origin])
    def test_allowed_origin_get_receives_cors_header_without_credentials(self):
        response = Client().get("/api/health/", HTTP_ORIGIN=self.allowed_origin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], self.allowed_origin)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    @override_settings(CORS_ALLOWED_ORIGINS=[allowed_origin])
    def test_disallowed_origin_receives_no_cors_allow_origin_header(self):
        response = Client().get(
            "/api/health/",
            HTTP_ORIGIN="https://other.private.example",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", response)

    @override_settings(CORS_ALLOWED_ORIGINS=[allowed_origin])
    def test_preflight_allows_only_configured_api_method_and_headers(self):
        response = Client().options(
            "/api/reviews",
            HTTP_ORIGIN=self.allowed_origin,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="PATCH",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], self.allowed_origin)
        self.assertNotIn("Access-Control-Allow-Credentials", response)
        self.assertIn("PATCH", response["Access-Control-Allow-Methods"])
        self.assertIn("PUT", response["Access-Control-Allow-Methods"])
        self.assertEqual(
            response["Access-Control-Allow-Headers"],
            "authorization, content-type",
        )
        self.assertNotIn("TRACE", response["Access-Control-Allow-Methods"])

    @override_settings(CORS_ALLOWED_ORIGINS=[allowed_origin])
    def test_disallowed_origin_preflight_has_no_cors_permission(self):
        response = Client().options(
            "/api/reviews",
            HTTP_ORIGIN="https://other.private.example",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)
        self.assertNotIn("Access-Control-Allow-Credentials", response)

    @override_settings(CORS_ALLOWED_ORIGINS=[])
    def test_development_proxy_requests_do_not_need_an_allowlist(self):
        response = Client().get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Access-Control-Allow-Origin", response)
