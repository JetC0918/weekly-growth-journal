from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import CanonicalUsernameIdentity
from .serializers import canonical_username_digest, canonicalize_username


@receiver(pre_save)
def remember_previous_username(sender, instance, raw=False, using="default", **kwargs):
    if raw or sender is not get_user_model() or not instance.pk:
        return
    field_name = sender.USERNAME_FIELD
    instance._canonical_identity_previous_username = (
        sender._default_manager.using(using)
        .filter(pk=instance.pk)
        .values_list(field_name, flat=True)
        .first()
    )


@receiver(post_save)
def maintain_canonical_username_identity(sender, instance, created, raw=False, using="default", **kwargs):
    if raw or sender is not get_user_model():
        return

    username = instance.get_username()
    canonical = canonicalize_username(username)
    digest = canonical_username_digest(username)

    try:
        # The savepoint lets callers translate a uniqueness race without
        # leaving their surrounding transaction in a broken state.
        with transaction.atomic(using=using):
            identity, identity_created = CanonicalUsernameIdentity.objects.using(using).get_or_create(
                user_id=instance.pk,
                defaults={"canonical_username": canonical, "canonical_digest": digest},
            )
            if not identity_created and (
                identity.canonical_username != canonical or identity.canonical_digest != digest
            ):
                identity.canonical_username = canonical
                identity.canonical_digest = digest
                identity.save(using=using, update_fields=("canonical_username", "canonical_digest"))
    except IntegrityError:
        if created:
            # AbstractUser.save() is not wrapped in a transaction by default.
            # Remove a just-created user if its canonical identity was already
            # claimed, so createsuperuser and other manager callers fail closed.
            sender._default_manager.using(using).filter(pk=instance.pk).delete()
        else:
            previous_username = getattr(instance, "_canonical_identity_previous_username", None)
            if previous_username is not None:
                # The caller may catch IntegrityError inside an outer
                # transaction. Restore the row here so it cannot commit a new
                # username with the old indexed identity.
                sender._default_manager.using(using).filter(pk=instance.pk).update(
                    **{sender.USERNAME_FIELD: previous_username}
                )
        raise
