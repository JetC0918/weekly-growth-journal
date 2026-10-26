from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CredentialsSerializer
from .tokens import create_access_token


class PublicAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        credentials = serializer.validated_data
        username = credentials["username"].casefold()
        user_model = get_user_model()

        if user_model.objects.filter(username__iexact=username).exists():
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
        user_model = get_user_model()
        user = user_model.objects.filter(
            username__iexact=credentials["username"].casefold(),
            is_active=True,
        ).first()

        if user is None or not user.check_password(credentials["password"]):
            response = Response(
                {"detail": "Incorrect username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response["WWW-Authenticate"] = "Bearer"
            return response

        return Response(
            {
                "accessToken": create_access_token(user.pk),
                "tokenType": "bearer",
            },
            status=status.HTTP_200_OK,
        )
