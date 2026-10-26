from django.conf import settings
from django.db import models


class CanonicalUsernameIdentity(models.Model):
    """Indexed, unique canonical username lookup for authentication."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="canonical_username_identity",
    )
    canonical_username = models.TextField()
    canonical_digest = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.canonical_username
