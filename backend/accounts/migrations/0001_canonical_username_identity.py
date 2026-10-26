import hashlib
import unicodedata

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def canonicalize_username(value):
    return unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", value).casefold())


def canonical_digest(value):
    return hashlib.sha256(canonicalize_username(value).encode("utf-8")).hexdigest()


def populate_canonical_identities(apps, schema_editor):
    user_app, user_model = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(user_app, user_model)
    Identity = apps.get_model("accounts", "CanonicalUsernameIdentity")
    database = schema_editor.connection.alias
    rows = list(User.objects.using(database).values_list("pk", "username"))

    grouped = {}
    for user_id, username in rows:
        grouped.setdefault(canonicalize_username(username), []).append(user_id)

    duplicate_ids = sorted(
        user_id
        for account_ids in grouped.values()
        if len(account_ids) > 1
        for user_id in account_ids
    )
    if duplicate_ids:
        raise RuntimeError(
            "Cannot build canonical username identities: existing account IDs "
            f"{duplicate_ids} normalize to duplicate usernames. Reconcile these accounts "
            "manually, preserving their data, then rerun migrations."
        )

    identities = [
        Identity(
            user_id=account_ids[0],
            canonical_username=canonical,
            canonical_digest=canonical_digest(canonical),
        )
        for canonical, account_ids in grouped.items()
    ]
    Identity.objects.using(database).bulk_create(identities)


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="CanonicalUsernameIdentity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("canonical_username", models.TextField()),
                ("canonical_digest", models.CharField(max_length=64, unique=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="canonical_username_identity",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.RunPython(populate_canonical_identities, migrations.RunPython.noop),
    ]
