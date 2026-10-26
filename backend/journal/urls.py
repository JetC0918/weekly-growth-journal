from django.urls import path

from .views import (
    CommitmentBeforeView,
    CompleteReviewView,
    DeleteAllDataView,
    FollowUpSuggestionsView,
    InsightUpdateView,
    ReviewByWeekView,
    ReviewCommitmentView,
    ReviewDetailView,
    ReviewListCreateView,
    ReviewReportView,
)


urlpatterns = [
    path("reviews", ReviewListCreateView.as_view(), name="journal-reviews"),
    path("reviews/suggest-follow-ups", FollowUpSuggestionsView.as_view(), name="journal-follow-up-suggestions"),
    path("reviews/by-week/<str:week_start>", ReviewByWeekView.as_view(), name="journal-review-by-week"),
    path("reviews/<str:review_id>/complete", CompleteReviewView.as_view(), name="journal-review-complete"),
    path("reviews/<str:review_id>/report/<str:section>/insights/<str:insight_id>", InsightUpdateView.as_view(), name="journal-insight-update"),
    path("reviews/<str:review_id>/report", ReviewReportView.as_view(), name="journal-review-report"),
    path("reviews/<str:review_id>/commitment", ReviewCommitmentView.as_view(), name="journal-review-commitment"),
    path("reviews/<str:review_id>", ReviewDetailView.as_view(), name="journal-review-detail"),
    path("commitments/before", CommitmentBeforeView.as_view(), name="journal-commitment-before"),
    path("data", DeleteAllDataView.as_view(), name="journal-delete-all-data"),
]
