from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.config.telemetry import record_workflow_event

from .models import CanonicalUsernameIdentity
from .serializers import CredentialsSerializer, RegistrationSerializer, canonical_username_digest
from .tokens import create_access_token


class PublicAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credentials = serializer.validated_data
        username = credentials["username"]
        user_model = get_user_model()

        digest = canonical_username_digest(username)
        if CanonicalUsernameIdentity.objects.filter(canonical_digest=digest).exists():
            return Response(
                {"detail": "Username is already registered"},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                user = user_model.objects.create_user(
                    username=username,
                    password=credentials["password"],
                )
        except IntegrityError:
            # The normalized username and Django's unique constraint also make
            # concurrent case-only duplicate registrations resolve as conflicts.
            return Response(
                {"detail": "Username is already registered"},
                status=status.HTTP_409_CONFLICT,
            )

        record_workflow_event("account.registered")
        return Response(
            {
                "accessToken": create_access_token(user.pk),
                "tokenType": "bearer",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(PublicAuthView):
    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credentials = serializer.validated_data
        username = credentials["username"]
        identity = (
            CanonicalUsernameIdentity.objects.select_related("user")
            .filter(canonical_digest=canonical_username_digest(username), user__is_active=True)
            .first()
        )
        # The digest is an indexed lookup key; verify the full canonical value
        # too, so even a theoretical digest collision fails closed.
        user = identity.user if identity and identity.canonical_username == username else None

        if user is None or not user.check_password(credentials["password"]):
            record_workflow_event("account.login", "rejected")
            response = Response(
                {"detail": "Incorrect username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response["WWW-Authenticate"] = "Bearer"
            return response

        record_workflow_event("account.login")
        return Response(
            {
                "accessToken": create_access_token(user.pk),
                "tokenType": "bearer",
            },
            status=status.HTTP_200_OK,
        )
