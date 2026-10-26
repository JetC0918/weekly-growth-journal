from datetime import date
from uuid import UUID, uuid4

from django.db import DatabaseError, IntegrityError, transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.feedback.follow_ups import (
    FollowUpProviderError,
    ProviderNotConfigured,
    ReportProviderError,
    ReportProviderNotConfigured,
    suggest_follow_up_questions,
)
from backend.feedback.reports import (
    InsufficientReflectionContent,
    generate_report_data,
    merge_user_edits,
)
from backend.config.telemetry import record_workflow_event

from .models import Commitment, FeedbackReport, Review
from .serializers import (
    CommitmentInputSerializer,
    CommitmentSerializer,
    InsightPatchSerializer,
    ReportSerializer,
    ReviewSerializer,
    SaveReviewSerializer,
)


def _public_id(prefix):
    return f"{prefix}_{uuid4().hex}"


def _parse_id(value, prefix):
    try:
        raw = value.removeprefix(f"{prefix}_")
        return UUID(raw)
    except (ValueError, TypeError, AttributeError):
        return None


def _bad_request(detail="Request validation failed"):
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


def _null_response():
    return HttpResponse("null", content_type="application/json")


def _validated(serializer):
    if serializer.is_valid():
        return serializer.validated_data, None
    return None, _bad_request()


class JournalView(APIView):
    def handle_exception(self, exc):
        if isinstance(exc, ParseError):
            return _bad_request("Invalid JSON body")
        return super().handle_exception(exc)

    def get_review(self, request, public_id):
        parsed = _parse_id(public_id, "rev")
        if parsed is None:
            return None
        return Review.objects.filter(user=request.user, pk=parsed).first()

    def json_response(self, data, serializer_class, http_status=status.HTTP_200_OK):
        return Response(serializer_class(data).data, status=http_status)


class ReviewListCreateView(JournalView):
    def get(self, request):
        reviews = Review.objects.filter(user=request.user).order_by("-week_start")
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request):
        serializer = SaveReviewSerializer(data=request.data)
        payload, error = _validated(serializer)
        if error:
            return error
        raw_id = payload.pop("id", None)
        existing = None
        if raw_id:
            parsed_id = _parse_id(raw_id, "rev")
            if parsed_id is None:
                return _bad_request("Invalid review id")
            existing = Review.objects.filter(user=request.user, pk=parsed_id).first()
        if existing is None:
            existing = Review.objects.filter(user=request.user, week_start=payload["week_start"]).first()

        created = existing is None
        try:
            with transaction.atomic():
                if existing is not None:
                    locked_existing = Review.objects.select_for_update().filter(
                        user=request.user,
                        pk=existing.pk,
                    ).first()
                    if locked_existing is None:
                        return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
                    if FeedbackReport.objects.filter(review=locked_existing).exists():
                        # Any edit invalidates the report generated from the
                        # previous reflection snapshot.
                        FeedbackReport.objects.filter(review=locked_existing).delete()
                        locked_existing.status = Review.Status.DRAFT
                    for field, value in payload.items():
                        setattr(locked_existing, field, value)
                    locked_existing.save(update_fields=(*payload.keys(), "status", "updated_at"))
                    review = locked_existing
                    created = False
                else:
                    review = Review.objects.create(user=request.user, status=Review.Status.DRAFT, **payload)
        except IntegrityError:
            return _bad_request("A review already exists for this week")
        record_workflow_event("review.saved")
        return self.json_response(review, ReviewSerializer, status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ReviewByWeekView(JournalView):
    def get(self, request, week_start):
        try:
            week = date.fromisoformat(week_start)
        except ValueError:
            return _bad_request("Invalid weekStart")
        review = Review.objects.filter(user=request.user, week_start=week).first()
        return self.json_response(review, ReviewSerializer) if review else _null_response()


class ReviewDetailView(JournalView):
    def get(self, request, review_id):
        review = self.get_review(request, review_id)
        return self.json_response(review, ReviewSerializer) if review else _null_response()

    def delete(self, request, review_id):
        parsed = _parse_id(review_id, "rev")
        if parsed is not None:
            with transaction.atomic():
                review = Review.objects.select_for_update().filter(user=request.user, pk=parsed).first()
                if review:
                    review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowUpSuggestionsView(JournalView):
    def post(self, request):
        serializer = SaveReviewSerializer(data=request.data)
        payload, error = _validated(serializer)
        if error:
            return error
        try:
            questions = suggest_follow_up_questions(payload)
        except ProviderNotConfigured as error:
            record_workflow_event("ai.follow_up", "not_configured")
            return Response({"detail": error.detail}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except FollowUpProviderError as error:
            record_workflow_event("ai.follow_up", "failed")
            return Response({"detail": error.detail}, status=status.HTTP_502_BAD_GATEWAY)
        record_workflow_event("ai.follow_up")
        return Response(questions)


class CompleteReviewView(JournalView):
    def post(self, request, review_id):
        review = self.get_review(request, review_id)
        if review is None:
            return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

        history = list(
            Review.objects.filter(
                user=request.user,
                status=Review.Status.COMPLETED,
                week_start__lt=review.week_start,
            )
            .order_by("-week_start")[:5]
        )
        try:
            report_data = generate_report_data(review, history)
        except InsufficientReflectionContent as error:
            record_workflow_event("review.completed", "insufficient_content")
            return Response({"detail": error.detail}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ReportProviderNotConfigured as error:
            record_workflow_event("review.completed", "provider_not_configured")
            return Response({"detail": error.detail}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ReportProviderError as error:
            record_workflow_event("review.completed", "provider_failed")
            return Response({"detail": error.detail}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            with transaction.atomic():
                locked_review = Review.objects.select_for_update().filter(
                    pk=review.pk,
                    user=request.user,
                ).first()
                if locked_review is None:
                    record_workflow_event("review.completed", "deleted_during_generation")
                    return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
                snapshot_changed = (
                    locked_review.updated_at != review.updated_at
                    or locked_review.week_start != review.week_start
                    or locked_review.answers != review.answers
                    or locked_review.free_writing != review.free_writing
                    or locked_review.follow_ups != review.follow_ups
                    or locked_review.previous_action != review.previous_action
                )
                if snapshot_changed:
                    record_workflow_event("review.completed", "changed_during_generation")
                    return Response(
                        {"detail": "Review changed while its report was being generated; please try again"},
                        status=status.HTTP_409_CONFLICT,
                    )
                existing_report = FeedbackReport.objects.filter(review=locked_review).first()
                report_data = merge_user_edits(existing_report, report_data)
                report, _ = FeedbackReport.objects.update_or_create(
                    review=locked_review,
                    defaults=report_data,
                )
                locked_review.status = Review.Status.COMPLETED
                locked_review.save()
        except DatabaseError:
            record_workflow_event("review.completed", "persistence_failed")
            return Response(
                {"detail": ReportProviderError.detail},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        record_workflow_event("review.completed")
        return self.json_response(report, ReportSerializer)


class ReviewReportView(JournalView):
    def get(self, request, review_id):
        review = self.get_review(request, review_id)
        report = FeedbackReport.objects.filter(review=review).first() if review else None
        return self.json_response(report, ReportSerializer) if report else _null_response()


class InsightUpdateView(JournalView):
    def patch(self, request, review_id, section, insight_id):
        if section not in {"takeaways", "strengths", "challenges", "patterns"}:
            return Response({"detail": "Insight not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = InsightPatchSerializer(data=request.data)
        changes, error = _validated(serializer)
        if error:
            if not request.data:
                return _bad_request("At least one field is required")
            return error
        if any(value is None for value in changes.values()):
            return _bad_request("Insight patch values cannot be null")
        review = self.get_review(request, review_id)
        report = FeedbackReport.objects.filter(review=review).first() if review else None
        if report is None:
            return Response({"detail": "Insight not found"}, status=status.HTTP_404_NOT_FOUND)
        insights = getattr(report, section)
        match = next((item for item in insights if item.get("id") == insight_id), None)
        if match is None:
            return Response({"detail": "Insight not found"}, status=status.HTTP_404_NOT_FOUND)
        match.update(changes)
        setattr(report, section, insights)
        report.save(update_fields=(section,))
        record_workflow_event("insight.updated")
        return self.json_response(report, ReportSerializer)


class ReviewCommitmentView(JournalView):
    def get(self, request, review_id):
        review = self.get_review(request, review_id)
        commitment = Commitment.objects.filter(review=review).first() if review else None
        return self.json_response(commitment, CommitmentSerializer) if commitment else _null_response()

    def put(self, request, review_id):
        review = self.get_review(request, review_id)
        if review is None:
            return Response({"detail": "Review not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommitmentInputSerializer(data=request.data)
        payload, error = _validated(serializer)
        if error:
            return error
        text = payload["text"].strip()
        if not text:
            return _bad_request("Commitment cannot be empty")
        commitment, _ = Commitment.objects.update_or_create(
            review=review,
            defaults={"text": text, "measure": payload["measure"].strip()},
        )
        record_workflow_event("commitment.saved")
        return self.json_response(commitment, CommitmentSerializer)


class CommitmentBeforeView(JournalView):
    def get(self, request):
        raw_week_start = request.query_params.get("weekStart")
        try:
            requested_week = date.fromisoformat(raw_week_start or "")
        except ValueError:
            return _bad_request("Invalid weekStart")
        commitment = Commitment.objects.filter(
            review__user=request.user,
            review__week_start__lt=requested_week,
        ).select_related("review").order_by("-review__week_start").first()
        return self.json_response(commitment, CommitmentSerializer) if commitment else _null_response()


class DeleteAllDataView(JournalView):
    def delete(self, request):
        Review.objects.filter(user=request.user).delete()
        record_workflow_event("journal.deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
