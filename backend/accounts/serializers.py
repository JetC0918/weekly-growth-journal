from collections.abc import Mapping

from rest_framework import serializers


class CredentialsSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=1, max_length=100, trim_whitespace=False)
    password = serializers.CharField(
        min_length=8,
        max_length=200,
        trim_whitespace=False,
        write_only=True,
    )

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
