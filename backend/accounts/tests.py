from unittest.mock import patch
from importlib import import_module

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, tag
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.views import APIView

from backend.accounts.tokens import TOKEN_LIFETIME_SECONDS, create_access_token
from backend.accounts.models import CanonicalUsernameIdentity


class ProtectedIdentityView(APIView):
    def get(self, request):
        return Response({"userId": request.user.pk})


class HealthEndpointTests(SimpleTestCase):
    def test_health_returns_json_success_without_authentication(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


@tag("integration")
class AuthenticationAPITests(APITestCase):
    def _protected_response(self, authorization=None):
        request = APIRequestFactory().get(
            "/api/protected-test/",
            HTTP_AUTHORIZATION=authorization or "",
        )
        return ProtectedIdentityView.as_view()(request)

    def _register(self, username="GrowthUser", password="private-pass-123"):
        return self.client.post(
            "/api/auth/register",
            {"username": username, "password": password},
            format="json",
        )

    def test_registration_uses_django_password_hashing_and_issues_a_token(self):
        response = self._register()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["tokenType"], "bearer")
        self.assertTrue(response.data["accessToken"])

        user = get_user_model().objects.get(username="growthuser")
        self.assertNotEqual(user.password, "private-pass-123")
        self.assertTrue(user.check_password("private-pass-123"))
        self.assertEqual(TOKEN_LIFETIME_SECONDS, 24 * 60 * 60)

    def test_case_insensitive_duplicate_registration_returns_conflict(self):
        self.assertEqual(self._register("GrowthUser").status_code, 201)

        response = self._register("GROWTHUSER")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, {"detail": "Username is already registered"})

    def test_registration_and_login_are_public_even_with_a_bad_bearer_header(self):
        registered = self.client.post(
            "/api/auth/register",
            {"username": "public-user", "password": "private-pass-123"},
            format="json",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        self.assertEqual(registered.status_code, 201)

        login = self.client.post(
            "/api/auth/login",
            {"username": "PUBLIC-USER", "password": "private-pass-123"},
            format="json",
            HTTP_AUTHORIZATION="Bearer invalid-token",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["tokenType"], "bearer")
        self.assertTrue(login.data["accessToken"])

    def test_invalid_login_returns_documented_unauthorized_response(self):
        self._register()

        for credentials in (
            {"username": "GrowthUser", "password": "wrong-password"},
            {"username": "missing-user", "password": "private-pass-123"},
        ):
            with self.subTest(username=credentials["username"]):
                response = self.client.post("/api/auth/login", credentials, format="json")
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.data, {"detail": "Incorrect username or password"})
                self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_invalid_credentials_body_uses_fastapi_422_validation_shape(self):
        response = self.client.post(
            "/api/auth/register",
            {"username": "x" * 101, "password": "short", "extra": "forbidden"},
            format="json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertIsInstance(response.data["detail"], list)
        locations = [error["loc"] for error in response.data["detail"]]
        self.assertIn(["body", "extra"], locations)
        self.assertIn(["body", "password"], locations)
        self.assertTrue(all({"loc", "msg", "type"}.issubset(error) for error in response.data["detail"]))

    def test_registration_enforces_configured_django_password_validators(self):
        response = self._register("numeric-password", "12345678")

        self.assertEqual(response.status_code, 422)
        self.assertTrue(any(error["loc"] == ["body", "password"] for error in response.data["detail"]))
        self.assertFalse(get_user_model().objects.filter(username="numeric-password").exists())

    def test_numeric_username_is_normalized_before_password_similarity_validation(self):
        response = self._register("31415.9265", "31415.9265")

        self.assertEqual(response.status_code, 422)
        self.assertFalse(get_user_model().objects.filter(username="31415.9265").exists())

    def test_compatibility_equivalent_username_is_canonicalized_for_registration_and_login(self):
        registered = self._register("audituser")

        self.assertEqual(registered.status_code, 201)
        duplicate = self._register("𝐀udituser")
        self.assertEqual(duplicate.status_code, 409)

        login = self.client.post(
            "/api/auth/login",
            {"username": "𝐀udituser", "password": "private-pass-123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(get_user_model().objects.filter(username="audituser").count(), 1)

    def test_canonical_identity_unique_constraint_rejects_compatibility_collision(self):
        user_model = get_user_model()
        first = user_model.objects.create_user(username="audituser", password="private-pass-123")

        with self.assertRaises(IntegrityError):
            user_model.objects.create_user(username="𝐀udituser", password="another-private-pass")

        self.assertFalse(user_model.objects.filter(username="𝐀udituser").exists())
        identity = CanonicalUsernameIdentity.objects.get(user=first)
        self.assertEqual(identity.canonical_username, "audituser")

    def test_rename_collision_restores_username_when_error_is_caught_inside_transaction(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="audituser", password="private-pass-123")
        renamed = user_model.objects.create_user(username="otheruser", password="another-private-pass")

        with transaction.atomic():
            renamed.username = "𝐀udituser"
            with self.assertRaises(IntegrityError):
                renamed.save(update_fields=("username",))

        renamed.refresh_from_db()
        identity = CanonicalUsernameIdentity.objects.get(user=renamed)
        self.assertEqual(renamed.username, "otheruser")
        self.assertEqual(identity.canonical_username, "otheruser")


    def test_bearer_token_authentication_associates_the_authenticated_user(self):
        registration = self._register()
        user = get_user_model().objects.get(username="growthuser")

        response = self._protected_response(f"Bearer {registration.data['accessToken']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"userId": user.pk})

    def test_missing_malformed_tampered_expired_and_unknown_user_tokens_are_rejected(self):
        user = get_user_model().objects.create_user(
            username="protected-user",
            password="private-pass-123",
        )
        valid = create_access_token(user.pk)
        tampered = f"{valid.rsplit('.', maxsplit=1)[0]}.invalid-signature"
        with self.settings(TOKEN_SIGNING_KEY="test-signing-key"):
            # A token signed with a different key exercises signature tampering.
            tampered_key = create_access_token(user.pk)
        with patch("backend.accounts.tokens.TOKEN_LIFETIME_SECONDS", 0):
            expired = create_access_token(user.pk)

        invalid_authorizations = (
            None,
            "Basic credentials",
            "Bearer",
            "Bearer malformed-token",
            f"Bearer {tampered}",
            f"Bearer {tampered_key}",
            f"Bearer {expired}",
            f"Bearer {create_access_token(999999999)}",
        )
        for authorization in invalid_authorizations:
            with self.subTest(authorization=authorization):
                response = self._protected_response(authorization)
                self.assertEqual(response.status_code, 401)
                self.assertIn(response.data["detail"], {
                    "Bearer token required",
                    "Invalid or expired bearer token",
                })
                self.assertEqual(response["WWW-Authenticate"], "Bearer")


class CanonicalIdentityMigrationTests(SimpleTestCase):
    def test_backfill_fails_with_account_ids_for_existing_canonical_collisions(self):
        migration = import_module("backend.accounts.migrations.0001_canonical_username_identity")

        class Rows:
            def using(self, alias):
                return self

            def values_list(self, *fields):
                return [(13, "audituser"), (27, "𝐀udituser")]

        class FakeUser:
            objects = Rows()

        class IdentityRows:
            def using(self, alias):
                return self

            def bulk_create(self, identities):
                raise AssertionError("No identity rows should be written for a collision")

        class FakeIdentity:
            objects = IdentityRows()

        class Registry:
            def get_model(self, app_label, model_name):
                if (app_label, model_name) == ("auth", "User"):
                    return FakeUser
                if (app_label, model_name) == ("accounts", "CanonicalUsernameIdentity"):
                    return FakeIdentity
                raise AssertionError("Unexpected model")

        class Connection:
            alias = "default"

        class SchemaEditor:
            connection = Connection()

        with self.assertRaisesRegex(RuntimeError, r"\[13, 27\]"):
            migration.populate_canonical_identities(Registry(), SchemaEditor())
