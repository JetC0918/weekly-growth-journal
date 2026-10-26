from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .tokens import decode_access_token


class SignedBearerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != b"bearer" or len(parts) == 1:
            raise AuthenticationFailed("Bearer token required")
        if len(parts) != 2:
            raise AuthenticationFailed("Invalid or expired bearer token")

        try:
            token = parts[1].decode("ascii")
        except UnicodeDecodeError as exc:
            raise AuthenticationFailed("Invalid or expired bearer token") from exc

        user_id = decode_access_token(token)
        if user_id is None:
            raise AuthenticationFailed("Invalid or expired bearer token")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=user_id, is_active=True)
        except (user_model.DoesNotExist, DjangoValidationError, TypeError, ValueError) as exc:
            raise AuthenticationFailed("Invalid or expired bearer token") from exc

        return user, token

    def authenticate_header(self, request):
        return "Bearer"
