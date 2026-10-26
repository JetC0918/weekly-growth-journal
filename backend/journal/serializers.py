from collections.abc import Mapping
from uuid import UUID

from rest_framework import serializers

from .models import Commitment, FeedbackReport, Review


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        extra_errors = {}
        if isinstance(data, Mapping):
            extra_errors = {
                key: [serializers.ErrorDetail("Extra inputs are not permitted", code="extra_forbidden")]
                for key in sorted(set(data) - set(self.fields))
            }
        try:
            validated_data = super().to_internal_value(data)
        except serializers.ValidationError as exc:
            field_errors = exc.detail if isinstance(exc.detail, Mapping) else {"non_field_errors": exc.detail}
            raise serializers.ValidationError({**field_errors, **extra_errors}) from exc
        if extra_errors:
            raise serializers.ValidationError(extra_errors)
        return validated_data


class AnswersSerializer(StrictSerializer):
    wentWell = serializers.CharField(allow_blank=True)
    didntGoWell = serializers.CharField(allow_blank=True)
    handledBetter = serializers.CharField(allow_blank=True)
    learned = serializers.CharField(allow_blank=True)
    doDifferently = serializers.CharField(allow_blank=True)


class FollowUpSerializer(StrictSerializer):
    question = serializers.CharField(allow_blank=True)
    answer = serializers.CharField(allow_blank=True)


class PreviousActionSerializer(StrictSerializer):
    commitmentId = serializers.CharField(allow_blank=True)
    attempted = serializers.ChoiceField(choices=("yes", "partly", "no", ""))
    whatHappened = serializers.CharField(allow_blank=True)
    learned = serializers.CharField(allow_blank=True)


class SaveReviewSerializer(StrictSerializer):
    id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    weekStart = serializers.DateField(source="week_start")
    answers = AnswersSerializer()
    freeWriting = serializers.CharField(source="free_writing", allow_blank=True)
    followUps = FollowUpSerializer(many=True, source="follow_ups")
    previousAction = PreviousActionSerializer(required=False, allow_null=True, source="previous_action")


class PrefixedUUIDField(serializers.Field):
    def __init__(self, prefix, **kwargs):
        self.prefix = prefix
        super().__init__(**kwargs)

    def to_representation(self, value):
        if isinstance(value, UUID):
            return f"{self.prefix}_{value.hex}"
        return f"{self.prefix}_{UUID(str(value)).hex}"

    def to_internal_value(self, data):
        try:
            raw = data.removeprefix(f"{self.prefix}_") if isinstance(data, str) else data
            return UUID(str(raw))
        except (ValueError, TypeError, AttributeError) as exc:
            raise serializers.ValidationError("Invalid identifier") from exc


class ReviewSerializer(serializers.ModelSerializer):
    id = PrefixedUUIDField("rev", read_only=True)
    weekStart = serializers.DateField(source="week_start")
    freeWriting = serializers.CharField(source="free_writing")
    followUps = FollowUpSerializer(many=True, source="follow_ups")
    previousAction = PreviousActionSerializer(allow_null=True, source="previous_action")
    createdAt = serializers.DateTimeField(source="created_at")
    updatedAt = serializers.DateTimeField(source="updated_at")

    class Meta:
        model = Review
        fields = ("id", "weekStart", "answers", "freeWriting", "followUps", "previousAction", "status", "createdAt", "updatedAt")


class InsightSerializer(StrictSerializer):
    id = serializers.CharField()
    text = serializers.CharField()
    kind = serializers.ChoiceField(choices=("observation", "hypothesis"))
    evidence = serializers.CharField()
    status = serializers.ChoiceField(choices=("pending", "accepted", "rejected"))
    correction = serializers.CharField(required=False, allow_null=True)


class ReportSerializer(serializers.ModelSerializer):
    id = PrefixedUUIDField("rep", read_only=True)
    reviewId = serializers.SerializerMethodField()
    takeaways = InsightSerializer(many=True)
    strengths = InsightSerializer(many=True)
    challenges = InsightSerializer(many=True)
    patterns = InsightSerializer(many=True)
    proposedAction = serializers.CharField(source="proposed_action")
    generatedAt = serializers.DateTimeField(source="generated_at")

    class Meta:
        model = FeedbackReport
        fields = ("id", "reviewId", "takeaways", "strengths", "challenges", "patterns", "proposedAction", "generatedAt")

    def get_reviewId(self, obj):
        return PrefixedUUIDField("rev").to_representation(obj.review_id)


class CommitmentInputSerializer(StrictSerializer):
    text = serializers.CharField(min_length=1)
    measure = serializers.CharField(allow_blank=True)


class CommitmentSerializer(serializers.ModelSerializer):
    id = PrefixedUUIDField("com", read_only=True)
    reviewId = serializers.SerializerMethodField()
    weekStart = serializers.DateField(source="review.week_start", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at")

    class Meta:
        model = Commitment
        fields = ("id", "reviewId", "weekStart", "text", "measure", "createdAt")

    def get_reviewId(self, obj):
        return PrefixedUUIDField("rev").to_representation(obj.review_id)


class InsightPatchSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=("pending", "accepted", "rejected"), required=False)
    correction = serializers.CharField(required=False, allow_null=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field is required")
        return attrs
