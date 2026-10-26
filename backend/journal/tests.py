from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, override_settings, tag
from rest_framework.test import APIClient

from backend.accounts.tokens import create_access_token
from .models import Commitment, FeedbackReport, Review


def review_payload(week_start):
    return {
        "weekStart": week_start.isoformat(),
        "answers": {
            "wentWell": "I made progress on the first draft.",
            "didntGoWell": "I delayed asking for help.",
            "handledBetter": "I could have asked sooner.",
            "learned": "Small steps help me start.",
            "doDifferently": "I will ask for help on Monday.",
        },
        "freeWriting": "I want to keep building momentum.",
        "followUps": [{"question": "What helped?", "answer": "A short plan."}],
    }


class FakeReportProvider:
    def generate_report(self, context):
        current = context["currentReview"]
        return {
            "takeaways": [
                {
                    "text": "A learning from this week.",
                    "kind": "observation",
                    "evidence": current["answers"]["learned"],
                }
            ],
            "strengths": [
                {
                    "text": "A positive action.",
                    "kind": "observation",
                    "evidence": current["answers"]["wentWell"],
                }
            ],
            "challenges": [],
            "patterns": [],
            "proposedAction": "Ask for help on Monday.",
        }


@tag("integration")
class JournalAPITests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="journal-user", password="test-password")
        self.other_user = user_model.objects.create_user(username="other-user", password="test-password")
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user.pk)}")
        self.other_client = APIClient()
        self.other_client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.other_user.pk)}")
        provider_patcher = patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(),
        )
        provider_patcher.start()
        self.addCleanup(provider_patcher.stop)

    def create_review(self, week_start=date(2025, 1, 6), client=None):
        response = (client or self.client).post("/api/reviews", review_payload(week_start), format="json")
        self.assertIn(response.status_code, (200, 201))
        return response.json()

    def test_reviews_persist_across_clients_and_upsert_preserves_id_and_created_at(self):
        week = date(2025, 1, 6)
        created = self.create_review(week)
        self.assertEqual(created["status"], "draft")
        self.assertTrue(created["id"].startswith("rev_"))
        self.assertEqual(Review.objects.filter(user=self.user, week_start=week).count(), 1)
        second_client = APIClient()
        second_client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user.pk)}")
        fetched = second_client.get(f"/api/reviews/{created['id']}").json()
        self.assertEqual(fetched, created)

        updated_payload = review_payload(week)
        updated_payload["freeWriting"] = "Edited reflection after reopening."
        updated = self.client.post("/api/reviews", updated_payload, format="json")

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["id"], created["id"])
        self.assertEqual(updated.json()["createdAt"], created["createdAt"])
        self.assertEqual(updated.json()["freeWriting"], "Edited reflection after reopening.")
        self.assertEqual(Review.objects.filter(user=self.user, week_start=week).count(), 1)

    def test_saving_an_edited_completed_review_invalidates_its_report(self):
        review = self.create_review()
        self.assertEqual(self.client.post(f"/api/reviews/{review['id']}/complete").status_code, 200)
        edited_payload = review_payload(date(2025, 1, 6))
        edited_payload["id"] = review["id"]
        edited_payload["freeWriting"] = "This reflection has changed."

        saved = self.client.post("/api/reviews", edited_payload, format="json")

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["status"], Review.Status.DRAFT)
        self.assertEqual(saved.json()["freeWriting"], "This reflection has changed.")
        self.assertFalse(FeedbackReport.objects.filter(review_id=_parse_public_id(review["id"])).exists())

    def test_review_list_ordering_and_week_lookup_are_private(self):
        older = self.create_review(date(2025, 1, 6))
        newer = self.create_review(date(2025, 1, 13))
        listed = self.client.get("/api/reviews").json()
        self.assertEqual([item["id"] for item in listed], [newer["id"], older["id"]])
        self.assertEqual(self.client.get("/api/reviews/by-week/2025-01-06").json(), older)
        self.assertEqual(self.other_client.get("/api/reviews/by-week/2025-01-06").json(), None)

    def test_invalid_journal_payloads_return_the_documented_bad_request_shape(self):
        extra_field = review_payload(date(2025, 1, 6))
        extra_field["unexpected"] = True
        invalid = self.client.post("/api/reviews", extra_field, format="json")
        malformed = self.client.generic("POST", "/api/reviews", data="{", content_type="application/json")

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(set(invalid.json()), {"detail"})
        self.assertEqual(malformed.status_code, 400)
        self.assertEqual(set(malformed.json()), {"detail"})

    def test_review_accepts_empty_strings_allowed_by_openapi(self):
        payload = review_payload(date(2025, 1, 6))
        payload["freeWriting"] = ""
        payload["answers"] = {field: "" for field in payload["answers"]}
        payload["followUps"] = [{"question": "", "answer": ""}]

        response = self.client.post("/api/reviews", payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["freeWriting"], "")
        self.assertEqual(set(response.json()["answers"].values()), {""})
        self.assertEqual(response.json()["followUps"], [{"question": "", "answer": ""}])

    def test_completion_report_and_commitment_persist_in_database(self):
        review = self.create_review()
        completed = self.client.post(f"/api/reviews/{review['id']}/complete")
        self.assertEqual(completed.status_code, 200)
        report = completed.json()
        self.assertTrue(report["id"].startswith("rep_"))
        self.assertEqual(report["reviewId"], review["id"])
        self.assertEqual(report["strengths"][0]["evidence"], "I made progress on the first draft.")
        self.assertEqual(FeedbackReport.objects.filter(review__user=self.user).count(), 1)
        self.assertEqual(Review.objects.get(pk=Review.objects.get(user=self.user).pk).status, Review.Status.COMPLETED)

        saved_commitment = self.client.put(
            f"/api/reviews/{review['id']}/commitment",
            {"text": "Practice asking early", "measure": "At Monday check-in"},
            format="json",
        )
        self.assertEqual(saved_commitment.status_code, 200)
        commitment = saved_commitment.json()
        self.assertTrue(commitment["id"].startswith("com_"))
        self.assertEqual(commitment["weekStart"], "2025-01-06")
        self.assertEqual(Commitment.objects.filter(review__user=self.user).count(), 1)

        other_instance = APIClient()
        other_instance.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user.pk)}")
        self.assertEqual(other_instance.get(f"/api/reviews/{review['id']}/report").json(), report)
        self.assertEqual(other_instance.get(f"/api/reviews/{review['id']}/commitment").json(), commitment)

    def test_completion_discards_provider_result_when_review_changes_during_generation(self):
        from backend.feedback.reports import generate_report_data as generate_from_snapshot

        review = self.create_review()
        model = Review.objects.get(pk=_parse_public_id(review["id"]))

        def edit_during_provider_call(snapshot, history):
            Review.objects.filter(pk=model.pk).update(
                free_writing="Edited while the report was being generated.",
                updated_at=model.updated_at + timedelta(seconds=1),
            )
            return generate_from_snapshot(snapshot, history)

        with patch("backend.journal.views.generate_report_data", side_effect=edit_during_provider_call):
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(FeedbackReport.objects.filter(review=model).exists())
        model.refresh_from_db()
        self.assertEqual(model.free_writing, "Edited while the report was being generated.")
        self.assertEqual(model.status, Review.Status.DRAFT)

    def test_completion_returns_not_found_when_review_is_deleted_during_generation(self):
        from backend.feedback.reports import generate_report_data as generate_from_snapshot

        review = self.create_review()
        model = Review.objects.get(pk=_parse_public_id(review["id"]))

        def delete_during_provider_call(snapshot, history):
            model.delete()
            return generate_from_snapshot(snapshot, history)

        with patch("backend.journal.views.generate_report_data", side_effect=delete_during_provider_call):
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Review.objects.filter(pk=model.pk).exists())
        self.assertFalse(FeedbackReport.objects.filter(review_id=model.pk).exists())

    def test_report_insight_update_and_follow_up_suggestions_use_injected_provider(self):
        payload = review_payload(date(2025, 1, 6))

        class FakeProvider:
            def suggest_questions(self, draft):
                self.draft = draft
                return ["What helped you make progress?"]

        provider = FakeProvider()
        with patch("backend.feedback.follow_ups.get_follow_up_provider", return_value=provider):
            suggestions = self.client.post("/api/reviews/suggest-follow-ups", payload, format="json")
        self.assertEqual(suggestions.status_code, 200)
        self.assertEqual(suggestions.json(), ["What helped you make progress?"])
        self.assertEqual(provider.draft["answers"], payload["answers"])
        review = self.create_review(date(2025, 1, 6))
        report = self.client.post(f"/api/reviews/{review['id']}/complete").json()
        insight = report["takeaways"][0]
        patched = self.client.patch(
            f"/api/reviews/{review['id']}/report/takeaways/insights/{insight['id']}",
            {"status": "accepted", "correction": "This reflects my week."},
            format="json",
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json()["takeaways"][0]["status"], "accepted")
        self.assertEqual(patched.json()["takeaways"][0]["correction"], "This reflects my week.")
        self.assertEqual(self.client.patch(
            f"/api/reviews/{review['id']}/report/takeaways/insights/{insight['id']}",
            {},
            format="json",
        ).status_code, 400)

    def test_commitment_before_is_strict_and_returns_most_recent_prior_commitment(self):
        first = self.create_review(date(2025, 1, 6))
        same_week = self.create_review(date(2025, 1, 13))
        later = self.create_review(date(2025, 1, 20))
        for review, text in ((first, "First"), (same_week, "Second"), (later, "Future")):
            response = self.client.put(
                f"/api/reviews/{review['id']}/commitment",
                {"text": text, "measure": "Once"},
                format="json",
            )
            self.assertEqual(response.status_code, 200)
        result = self.client.get("/api/commitments/before?weekStart=2025-01-20").json()
        self.assertEqual(result["text"], "Second")
        self.assertIsNone(self.client.get("/api/commitments/before?weekStart=2025-01-06").json())

    def test_other_user_cannot_read_change_or_delete_journal_records(self):
        review = self.create_review()
        report = self.client.post(f"/api/reviews/{review['id']}/complete").json()
        commitment = self.client.put(
            f"/api/reviews/{review['id']}/commitment",
            {"text": "Keep", "measure": "Weekly"},
            format="json",
        ).json()
        report_url = f"/api/reviews/{review['id']}/report"
        commitment_url = f"/api/reviews/{review['id']}/commitment"

        self.assertIsNone(self.other_client.get(f"/api/reviews/{review['id']}").json())
        self.assertIsNone(self.other_client.get(report_url).json())
        self.assertIsNone(self.other_client.get(commitment_url).json())
        self.assertEqual(self.other_client.post(f"/api/reviews/{review['id']}/complete").status_code, 404)
        self.assertEqual(self.other_client.put(commitment_url, {"text": "No", "measure": "No"}, format="json").status_code, 404)
        self.assertEqual(self.other_client.delete(f"/api/reviews/{review['id']}").status_code, 204)

        own_review = self.client.get(f"/api/reviews/{review['id']}").json()
        self.assertEqual(own_review["id"], review["id"])
        self.assertEqual(own_review["status"], Review.Status.COMPLETED)
        self.assertEqual(self.client.get(report_url).json(), report)
        self.assertEqual(self.client.get(commitment_url).json(), commitment)

    def test_review_delete_cascades_report_and_commitment(self):
        review = self.create_review()
        self.client.post(f"/api/reviews/{review['id']}/complete")
        self.client.put(f"/api/reviews/{review['id']}/commitment", {"text": "Keep", "measure": "Weekly"}, format="json")
        model = Review.objects.get(user=self.user)
        self.assertTrue(FeedbackReport.objects.filter(review=model).exists())
        self.assertTrue(Commitment.objects.filter(review=model).exists())

        self.assertEqual(self.client.delete(f"/api/reviews/{review['id']}").status_code, 204)
        self.assertFalse(Review.objects.filter(pk=model.pk).exists())
        self.assertFalse(FeedbackReport.objects.filter(review_id=model.pk).exists())
        self.assertFalse(Commitment.objects.filter(review_id=model.pk).exists())

    def test_delete_all_data_only_removes_current_users_records_and_preserves_accounts(self):
        own_review = self.create_review(date(2025, 1, 6))
        other_review = self.create_review(date(2025, 1, 13), client=self.other_client)
        own_model = Review.objects.get(pk=_parse_public_id(own_review["id"]))
        self.client.post(f"/api/reviews/{own_review['id']}/complete")
        self.client.put(f"/api/reviews/{own_review['id']}/commitment", {"text": "Keep", "measure": "Weekly"}, format="json")
        other_model = Review.objects.get(pk=_parse_public_id(other_review["id"]))
        self.other_client.post(f"/api/reviews/{other_review['id']}/complete")
        self.other_client.put(f"/api/reviews/{other_review['id']}/commitment", {"text": "Other", "measure": "Weekly"}, format="json")

        self.assertEqual(self.client.delete("/api/data").status_code, 204)
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
        self.assertFalse(Review.objects.filter(pk=own_model.pk).exists())
        self.assertFalse(FeedbackReport.objects.filter(review_id=own_model.pk).exists())
        self.assertFalse(Commitment.objects.filter(review_id=own_model.pk).exists())
        self.assertTrue(Review.objects.filter(pk=other_model.pk, user=self.other_user).exists())
        self.assertTrue(FeedbackReport.objects.filter(review_id=other_model.pk).exists())
        self.assertTrue(Commitment.objects.filter(review_id=other_model.pk).exists())

    def test_commitment_replacement_retains_identifier_and_creation_time(self):
        review = self.create_review()
        url = f"/api/reviews/{review['id']}/commitment"
        first = self.client.put(url, {"text": "Start", "measure": "Once"}, format="json").json()
        replacement = self.client.put(url, {"text": "Continue", "measure": "Twice"}, format="json").json()
        self.assertEqual(replacement["id"], first["id"])
        self.assertEqual(replacement["createdAt"], first["createdAt"])
        self.assertEqual(replacement["text"], "Continue")


@override_settings(DEBUG=True, AI_PROVIDER_MODE="fake", AI_API_KEY="")
@tag("integration")
class DeterministicWeeklyJourneyTests(TestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        user = get_user_model().objects.create_user(
            username="weekly-journey-user",
            password="test-password",
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(user.pk)}")

    def test_two_week_feedback_loop_persists_report_edit_commitment_and_outcome(self):
        first_payload = review_payload(date(2026, 10, 19))

        questions = self.client.post(
            "/api/reviews/suggest-follow-ups",
            first_payload,
            format="json",
        )
        self.assertEqual(questions.status_code, 200)
        self.assertTrue(questions.json())

        created = self.client.post("/api/reviews", first_payload, format="json")
        self.assertEqual(created.status_code, 201)
        first_review = created.json()
        reopened = self.client.get(f"/api/reviews/{first_review['id']}")
        self.assertEqual(reopened.status_code, 200)
        self.assertEqual(reopened.json(), first_review)

        completed = self.client.post(f"/api/reviews/{first_review['id']}/complete")
        self.assertEqual(completed.status_code, 200)
        report = completed.json()
        reflection_text = {
            *first_payload["answers"].values(),
            first_payload["freeWriting"],
            first_payload["followUps"][0]["question"],
            first_payload["followUps"][0]["answer"],
        }
        insights = [
            insight
            for section in ("takeaways", "strengths", "challenges", "patterns")
            for insight in report[section]
        ]
        self.assertTrue(insights)
        self.assertTrue(all(insight["evidence"] in reflection_text for insight in insights))
        insight = report["takeaways"][0]
        edited_report = self.client.patch(
            f"/api/reviews/{first_review['id']}/report/takeaways/insights/{insight['id']}",
            {"status": "accepted", "correction": "This matches what I want to practice."},
            format="json",
        )
        self.assertEqual(edited_report.status_code, 200)

        saved_commitment = self.client.put(
            f"/api/reviews/{first_review['id']}/commitment",
            {"text": "Ask for help early", "measure": "Ask once before Wednesday"},
            format="json",
        )
        self.assertEqual(saved_commitment.status_code, 200)
        commitment = saved_commitment.json()

        retrieved_report = self.client.get(f"/api/reviews/{first_review['id']}/report")
        retrieved_commitment = self.client.get(f"/api/reviews/{first_review['id']}/commitment")
        self.assertEqual(retrieved_report.json()["takeaways"][0]["correction"], "This matches what I want to practice.")
        self.assertEqual(retrieved_commitment.json(), commitment)

        next_payload = review_payload(date(2026, 10, 26))
        next_payload["previousAction"] = {
            "commitmentId": commitment["id"],
            "attempted": "partly",
            "whatHappened": "I asked once before the Wednesday check-in.",
            "learned": "Asking sooner gave me more time to act.",
        }
        next_saved = self.client.post("/api/reviews", next_payload, format="json")
        self.assertEqual(next_saved.status_code, 201)
        next_review = self.client.get(f"/api/reviews/{next_saved.json()['id']}")
        self.assertEqual(next_review.status_code, 200)
        self.assertEqual(next_review.json()["previousAction"], next_payload["previousAction"])
        prior_commitment = self.client.get("/api/commitments/before?weekStart=2026-10-26")
        self.assertEqual(prior_commitment.status_code, 200)
        self.assertEqual(prior_commitment.json(), commitment)


def _parse_public_id(value):
    from uuid import UUID

    return UUID(value.removeprefix("rev_"))
