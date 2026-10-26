from collections.abc import Mapping
from hashlib import sha256
import unicodedata

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


def canonicalize_username(value):
    """Return the one representation used for username policy and lookup."""
    return unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", value).casefold())


def canonical_username_digest(value):
    return sha256(canonicalize_username(value).encode("utf-8")).hexdigest()


class CredentialsSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=1, max_length=100, trim_whitespace=False)
    password = serializers.CharField(
        min_length=8,
        max_length=200,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_username(self, value):
        canonical = canonicalize_username(value)
        if len(canonical) > 100:
            raise serializers.ValidationError("Ensure this field has no more than 100 characters.")
        return canonical

    def to_internal_value(self, data):
        extra_errors = {}
        if isinstance(data, Mapping):
            extra_fields = set(data) - set(self.fields)
            extra_errors = {
                name: [serializers.ErrorDetail("Extra inputs are not permitted", code="extra_forbidden")]
                for name in sorted(extra_fields)
            }

        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as exc:
            field_errors = exc.detail if isinstance(exc.detail, Mapping) else {"non_field_errors": exc.detail}
            raise serializers.ValidationError({**field_errors, **extra_errors}) from exc

        if extra_errors:
            raise serializers.ValidationError(extra_errors)
        return validated_data


class RegistrationSerializer(CredentialsSerializer):
    def validate_password(self, value):
        username = self.initial_data.get("username") if isinstance(self.initial_data, Mapping) else None
        # Username fields are validated before password fields, but password
        # similarity must use the normalized value DRF will actually accept.
        canonical = canonicalize_username(str(username)) if username is not None else None
        user = get_user_model()(username=canonical) if canonical else None
        try:
            validate_password(value, user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return value
