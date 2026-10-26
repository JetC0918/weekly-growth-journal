from uuid import uuid4

from django.conf import settings
from django.db import models


class Review(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal_reviews")
    week_start = models.DateField()
    answers = models.JSONField()
    free_writing = models.TextField()
    follow_ups = models.JSONField(default=list)
    previous_action = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "week_start"), name="journal_review_user_week_unique")]
        indexes = [models.Index(fields=("user", "-week_start"), name="journal_review_user_week_idx")]
        ordering = ("-week_start",)


class FeedbackReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="report")
    takeaways = models.JSONField(default=list)
    strengths = models.JSONField(default=list)
    challenges = models.JSONField(default=list)
    patterns = models.JSONField(default=list)
    proposed_action = models.TextField(blank=True)
    generated_at = models.DateTimeField()


class Commitment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="commitment")
    text = models.TextField()
    measure = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

