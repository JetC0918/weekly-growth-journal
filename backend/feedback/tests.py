import json
from datetime import date, timedelta
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.test import SimpleTestCase, override_settings, tag
from rest_framework.test import APITestCase

from backend.accounts.tokens import create_access_token
from backend.journal.models import Commitment, FeedbackReport, Review
from backend.feedback.follow_ups import (
    FollowUpProviderError,
    OpenAICompatibleProvider,
    ProviderNotConfigured,
    ReportProviderNotConfigured,
    ReportProviderError,
    get_follow_up_provider,
    get_report_provider,
    suggest_follow_up_questions,
)


def draft_payload():
    return {
        "weekStart": "2026-10-19",
        "answers": {
            "wentWell": "I made progress on the draft.",
            "didntGoWell": "I postponed asking for help.",
            "handledBetter": "I could have asked sooner.",
            "learned": "Planning makes it easier to begin.",
            "doDifferently": "Ask for help early next week.",
        },
        "freeWriting": "I want to keep practicing.",
        "followUps": [{"question": "What helped?", "answer": "I made a small plan."}],
    }


def provider_payload(content):
    return json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]}).encode()


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class FakeProvider:
    def __init__(self, questions):
        self.questions = questions
        self.draft = None

    def suggest_questions(self, draft):
        self.draft = draft
        return self.questions


class FakeReportProvider:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.context = None

    def generate_report(self, context):
        self.context = context
        if self.error:
            raise self.error
        if self.output is not None:
            return self.output
        current = context["currentReview"]
        return {
            "takeaways": [
                {
                    "text": "A takeaway from this review.",
                    "kind": "observation",
                    "evidence": current["answers"]["learned"],
                }
            ],
            "strengths": [
                {
                    "text": "A strength from this review.",
                    "kind": "observation",
                    "evidence": current["answers"]["wentWell"],
                }
            ],
            "challenges": [],
            "patterns": [],
            "proposedAction": "Choose one small next step.",
        }


def valid_report_output():
    return FakeReportProvider().generate_report(
        {"currentReview": draft_payload(), "earlierReviews": []}
    )


class OpenAICompatibleProviderTests(SimpleTestCase):
    def make_provider(self, opener, *, api_key="test-provider-key"):
        return OpenAICompatibleProvider(
            base_url="https://ai.example.test/v1/",
            model="example-model",
            api_key=api_key,
            opener=opener,
        )

    def test_sends_openai_compatible_chat_request_and_limits_questions(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse(
                provider_payload(
                    {
                        "questions": [
                            "  First question?  ",
                            "Second question?",
                            "Third question?",
                            "Fourth question?",
                            " " * 3,
                            "x" * 201,
                        ]
                    }
                )
            )

        provider = self.make_provider(opener)
        questions = provider.suggest_questions(draft_payload())

        self.assertEqual(questions, ["First question?", "Second question?", "Third question?"])
        request = captured["request"]
        self.assertEqual(request.full_url, "https://ai.example.test/v1/chat/completions")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-provider-key")
        self.assertEqual(captured["timeout"], 15)
        body = json.loads(request.data)
        self.assertEqual(body["model"], "example-model")
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertIn("I made progress on the draft", body["messages"][1]["content"])
        self.assertNotIn("weekStart", body["messages"][1]["content"])

    def test_report_operation_reuses_openai_chat_completions_format(self):
        captured = {}
        output = {
            "takeaways": [],
            "strengths": [],
            "challenges": [],
            "patterns": [],
            "proposedAction": "Take one small step.",
        }

        def opener(request, timeout):
            captured["request"] = request
            return FakeResponse(provider_payload(output))

        provider = self.make_provider(opener)
        context = {"currentReview": draft_payload(), "earlierReviews": []}

        self.assertEqual(provider.generate_report(context), output)
        request = captured["request"]
        self.assertEqual(request.full_url, "https://ai.example.test/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-provider-key")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "example-model")
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertIn("currentReview", body["messages"][1]["content"])

    def test_missing_configuration_does_not_call_transport(self):
        with patch("backend.feedback.follow_ups.urlopen") as opener:
            provider = self.make_provider(opener, api_key=" ")
            with self.assertRaises(ProviderNotConfigured) as error:
                provider.suggest_questions(draft_payload())

        opener.assert_not_called()
        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("until an AI provider is configured", error.exception.detail)

    def test_timeout_http_failure_and_unusable_output_are_safe_provider_errors(self):
        for opener in (
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("private reflection and key")),
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                HTTPError("https://ai.example.test", 500, "private key", {}, BytesIO(b"private body"))
            ),
            lambda *_args, **_kwargs: FakeResponse(provider_payload({"questions": ["", 8]})),
            lambda *_args, **_kwargs: FakeResponse(b"not-json"),
        ):
            with self.subTest(opener=opener):
                with self.assertRaises(FollowUpProviderError) as error:
                    self.make_provider(opener).suggest_questions(draft_payload())
                self.assertEqual(error.exception.status_code, 502)
                self.assertEqual(
                    error.exception.detail,
                    "Follow-up suggestions are temporarily unavailable. Please try again later.",
                )
                self.assertNotIn("private", str(error.exception))


class DeterministicFakeProviderTests(SimpleTestCase):
    @override_settings(DEBUG=True, AI_PROVIDER_MODE="fake", AI_API_KEY="")
    def test_fake_mode_is_deterministic_and_report_evidence_is_exact_input(self):
        draft = draft_payload()
        follow_up_provider = get_follow_up_provider()
        report_provider = get_report_provider()
        context = {"currentReview": draft, "earlierReviews": []}

        questions = follow_up_provider.suggest_questions(draft)
        report = report_provider.generate_report(context)

        self.assertEqual(
            questions,
            [
                "What is one small step you want to try next week?",
                "What could make that step easier to start?",
            ],
        )
        self.assertEqual(report, report_provider.generate_report(context))
        available_text = {
            *draft["answers"].values(),
            draft["freeWriting"],
            draft["followUps"][0]["question"],
            draft["followUps"][0]["answer"],
        }
        all_insights = [
            insight
            for section in ("takeaways", "strengths", "challenges", "patterns")
            for insight in report[section]
        ]
        self.assertTrue(all_insights)
        self.assertTrue(all(insight["evidence"] in available_text for insight in all_insights))

    @override_settings(DEBUG=False, AI_PROVIDER_MODE="fake", AI_API_KEY="")
    def test_fake_mode_fails_safely_when_debug_is_disabled(self):
        with patch("backend.feedback.follow_ups.urlopen") as network:
            with self.assertRaises(ProviderNotConfigured):
                get_follow_up_provider()
            with self.assertRaises(ReportProviderNotConfigured):
                get_report_provider()
        network.assert_not_called()


@tag("integration")
class FakeProviderEndpointGatingTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="fake-mode-user", password="test-password")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(user.pk)}")

    @override_settings(DEBUG=False, AI_PROVIDER_MODE="fake", AI_API_KEY="")
    def test_fake_provider_is_disabled_for_followups_and_reports_when_debug_is_false(self):
        draft = draft_payload()
        draft_response = self.client.post("/api/reviews", draft, format="json")
        self.assertEqual(draft_response.status_code, 201)

        with patch("backend.feedback.follow_ups.urlopen") as network:
            follow_ups = self.client.post("/api/reviews/suggest-follow-ups", draft, format="json")
            report = self.client.post(f"/api/reviews/{draft_response.json()['id']}/complete")

        self.assertEqual(follow_ups.status_code, 503)
        self.assertEqual(report.status_code, 503)
        network.assert_not_called()


class FollowUpProviderInputTests(SimpleTestCase):
    def test_empty_draft_skips_the_provider(self):
        provider = FakeProvider(["not called"])
        empty = draft_payload()
        empty["answers"] = {key: "  " for key in empty["answers"]}
        empty["freeWriting"] = "\t"
        empty["followUps"] = [{"question": "A question", "answer": "  "}]

        self.assertEqual(suggest_follow_up_questions(empty, provider), [])
        self.assertIsNone(provider.draft)

    def test_fake_provider_can_supply_deterministic_questions_from_draft(self):
        provider = FakeProvider(["What would make the next step easier?"])

        result = suggest_follow_up_questions(draft_payload(), provider)

        self.assertEqual(result, ["What would make the next step easier?"])
        self.assertEqual(
            provider.draft,
            {
                "answers": draft_payload()["answers"],
                "freeWriting": draft_payload()["freeWriting"],
                "followUps": draft_payload()["followUps"],
                "previousAction": None,
            },
        )


@tag("integration")
class FollowUpEndpointTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="follow-up-user", password="test-password")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(user.pk)}")

    def test_empty_draft_returns_empty_array_without_building_provider(self):
        payload = draft_payload()
        payload["answers"] = {key: " " for key in payload["answers"]}
        payload["freeWriting"] = ""
        payload["followUps"] = [{"question": "Earlier question?", "answer": " "}]

        with patch("backend.feedback.follow_ups.get_follow_up_provider") as factory:
            response = self.client.post("/api/reviews/suggest-follow-ups", payload, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        factory.assert_not_called()

    def test_missing_api_key_returns_safe_503_without_network_call(self):
        with override_settings(AI_BASE_URL="https://api.openai.com/v1", AI_MODEL="example-model", AI_API_KEY=""):
            with patch("backend.feedback.follow_ups.urlopen") as network:
                response = self.client.post(
                    "/api/reviews/suggest-follow-ups", draft_payload(), format="json"
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Follow-up suggestions are unavailable until an AI provider is configured."},
        )
        network.assert_not_called()

    def test_fake_provider_generates_questions_for_the_authenticated_draft(self):
        provider = FakeProvider(["What was within your control?"])
        with patch("backend.feedback.follow_ups.get_follow_up_provider", return_value=provider):
            response = self.client.post(
                "/api/reviews/suggest-follow-ups", draft_payload(), format="json"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["What was within your control?"])
        self.assertEqual(provider.draft["answers"], draft_payload()["answers"])

    def test_provider_failure_and_invalid_output_return_safe_502(self):
        failing_provider = self.make_provider(lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("secret")))
        with override_settings(AI_BASE_URL="https://ai.example.test/v1", AI_MODEL="model", AI_API_KEY="not-return-me"):
            with patch("backend.feedback.follow_ups.get_follow_up_provider", return_value=failing_provider):
                failure = self.client.post(
                    "/api/reviews/suggest-follow-ups", draft_payload(), format="json"
                )
            invalid_provider = self.make_provider(
                lambda *_args, **_kwargs: FakeResponse(provider_payload({"questions": ["", "x" * 201]}))
            )
            with patch("backend.feedback.follow_ups.get_follow_up_provider", return_value=invalid_provider):
                invalid = self.client.post(
                    "/api/reviews/suggest-follow-ups", draft_payload(), format="json"
                )

        expected = "Follow-up suggestions are temporarily unavailable. Please try again later."
        for response in (failure, invalid):
            self.assertEqual(response.status_code, 502)
            self.assertEqual(response.json(), {"detail": expected})
            self.assertNotIn("not-return-me", response.content.decode())
            self.assertNotIn("I made progress", response.content.decode())

    def make_provider(self, opener):
        return OpenAICompatibleProvider(
            base_url="https://ai.example.test/v1",
            model="example-model",
            api_key="not-return-me",
            opener=opener,
        )


@tag("integration")
class ReportGenerationAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="report-user", password="test-password")
        self.other_user = user_model.objects.create_user(username="other-report-user", password="test-password")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user.pk)}")

    def create_draft(self, payload=None, *, user=None):
        if user is not None:
            client = self.client_for(user)
        else:
            client = self.client
        response = client.post("/api/reviews", payload or draft_payload(), format="json")
        self.assertIn(response.status_code, (200, 201))
        return response.json()

    def client_for(self, user):
        from rest_framework.test import APIClient

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {create_access_token(user.pk)}")
        return client

    def test_success_generates_backend_owned_fields_and_persists_atomically(self):
        review = self.create_draft()
        provider = FakeReportProvider()

        with patch("backend.feedback.reports.get_report_provider", return_value=provider):
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 200)
        report = response.json()
        self.assertTrue(report["id"].startswith("rep_"))
        self.assertEqual(report["reviewId"], review["id"])
        self.assertTrue(report["generatedAt"])
        self.assertEqual(report["takeaways"][0]["status"], "pending")
        self.assertTrue(report["takeaways"][0]["id"].startswith("ins_"))
        self.assertEqual(report["takeaways"][0]["evidence"], draft_payload()["answers"]["learned"])
        stored_review = Review.objects.get(pk=review["id"].removeprefix("rev_"))
        self.assertEqual(stored_review.status, Review.Status.COMPLETED)
        self.assertEqual(FeedbackReport.objects.filter(review=stored_review).count(), 1)
        self.assertEqual(self.client.get(f"/api/reviews/{review['id']}/report").json(), report)

    def test_context_contains_only_five_most_recent_same_user_earlier_completed_reviews(self):
        current_week = date.fromisoformat(draft_payload()["weekStart"])
        current = self.create_draft()
        for weeks_earlier in range(1, 8):
            week = current_week - timedelta(weeks=weeks_earlier)
            review = Review.objects.create(
                user=self.user,
                week_start=week,
                answers={**draft_payload()["answers"], "learned": f"history evidence {weeks_earlier}"},
                free_writing="",
                follow_ups=[],
                status=Review.Status.COMPLETED,
            )

        Review.objects.create(
            user=self.user,
            week_start=current_week - timedelta(weeks=8),
            answers=draft_payload()["answers"],
            free_writing="older draft should be excluded",
            follow_ups=[],
            status=Review.Status.DRAFT,
        )
        Review.objects.create(
            user=self.user,
            week_start=current_week + timedelta(weeks=1),
            answers=draft_payload()["answers"],
            free_writing="future completed should be excluded",
            follow_ups=[],
            status=Review.Status.COMPLETED,
        )
        Review.objects.create(
            user=self.other_user,
            week_start=current_week - timedelta(weeks=1),
            answers={**draft_payload()["answers"], "learned": "other user's private evidence"},
            free_writing="",
            follow_ups=[],
            status=Review.Status.COMPLETED,
        )
        output = valid_report_output()
        output["strengths"][0]["evidence"] = "history evidence 1"
        provider = FakeReportProvider(output=output)

        with patch("backend.feedback.reports.get_report_provider", return_value=provider):
            response = self.client.post(f"/api/reviews/{current['id']}/complete")

        self.assertEqual(response.status_code, 200)
        week_starts = [item["weekStart"] for item in provider.context["earlierReviews"]]
        expected_weeks = [
            (current_week - timedelta(weeks=weeks_earlier)).isoformat()
            for weeks_earlier in range(1, 6)
        ]
        self.assertEqual(week_starts, expected_weeks)
        self.assertEqual(len(week_starts), 5)
        self.assertEqual(response.json()["strengths"][0]["evidence"], "history evidence 1")

    def test_blank_review_returns_422_without_provider_call_or_state_change(self):
        payload = draft_payload()
        payload["answers"] = {key: " " for key in payload["answers"]}
        payload["freeWriting"] = "\t"
        payload["followUps"] = [{"question": "Question?", "answer": " "}]
        payload["previousAction"] = {
            "commitmentId": "past-commitment",
            "attempted": "yes",
            "whatHappened": "Some earlier context.",
            "learned": "A previous lesson.",
        }
        review = self.create_draft(payload)

        with patch("backend.feedback.reports.get_report_provider") as factory:
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 422)
        self.assertIn("at least one reflection", response.json()["detail"].lower())
        factory.assert_not_called()
        stored = Review.objects.get(pk=review["id"].removeprefix("rev_"))
        self.assertEqual(stored.status, Review.Status.DRAFT)
        self.assertFalse(FeedbackReport.objects.filter(review=stored).exists())

    def test_missing_configuration_returns_503_without_a_provider_request(self):
        review = self.create_draft()
        with override_settings(AI_BASE_URL="https://api.openai.com/v1", AI_MODEL="example-model", AI_API_KEY=""):
            with patch("backend.feedback.follow_ups.urlopen") as network:
                response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 503)
        self.assertIn("until an AI provider is configured", response.json()["detail"])
        network.assert_not_called()
        self.assertEqual(
            Review.objects.get(pk=review["id"].removeprefix("rev_")).status,
            Review.Status.DRAFT,
        )

    def test_invalid_evidence_and_provider_owned_fields_return_safe_502(self):
        review = self.create_draft()
        invalid_outputs = []
        invalid_evidence = valid_report_output()
        invalid_evidence["strengths"][0]["evidence"] = "text never supplied by this user"
        invalid_outputs.append(invalid_evidence)
        provider_field = valid_report_output()
        provider_field["takeaways"][0]["status"] = "accepted"
        invalid_outputs.append(provider_field)

        for invalid_output in invalid_outputs:
            with self.subTest(output=invalid_output):
                with patch(
                    "backend.feedback.reports.get_report_provider",
                    return_value=FakeReportProvider(output=invalid_output),
                ):
                    response = self.client.post(f"/api/reviews/{review['id']}/complete")
                self.assertEqual(response.status_code, 502)
                self.assertEqual(
                    response.json(),
                    {"detail": ReportProviderError.detail},
                )

        stored = Review.objects.get(pk=review["id"].removeprefix("rev_"))
        self.assertEqual(stored.status, Review.Status.DRAFT)
        self.assertFalse(FeedbackReport.objects.filter(review=stored).exists())

    def test_failed_regeneration_preserves_existing_report_and_completed_state(self):
        review = self.create_draft()
        with patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(),
        ):
            first = self.client.post(f"/api/reviews/{review['id']}/complete")
        self.assertEqual(first.status_code, 200)
        previous = FeedbackReport.objects.get(review_id=review["id"].removeprefix("rev_"))
        previous_snapshot = (previous.id, previous.generated_at, previous.takeaways)

        invalid = valid_report_output()
        invalid["takeaways"][0]["evidence"] = "not supported by supplied text"
        with patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(output=invalid),
        ):
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 502)
        stored = FeedbackReport.objects.get(review_id=review["id"].removeprefix("rev_"))
        self.assertEqual((stored.id, stored.generated_at, stored.takeaways), previous_snapshot)
        self.assertEqual(
            Review.objects.get(pk=review["id"].removeprefix("rev_")).status,
            Review.Status.COMPLETED,
        )

    def test_database_failure_rolls_back_report_update_and_review_status(self):
        review = self.create_draft()
        provider = FakeReportProvider()
        with patch("backend.feedback.reports.get_report_provider", return_value=provider):
            with patch("backend.journal.views.Review.save", side_effect=DatabaseError("private database detail")):
                response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("private database detail", response.content.decode())
        stored = Review.objects.get(pk=review["id"].removeprefix("rev_"))
        self.assertEqual(stored.status, Review.Status.DRAFT)
        self.assertFalse(FeedbackReport.objects.filter(review=stored).exists())

    def test_other_users_evidence_is_not_accepted_as_support(self):
        review = self.create_draft()
        other = Review.objects.create(
            user=self.other_user,
            week_start=date(2026, 10, 12),
            answers={**draft_payload()["answers"], "learned": "exclusive other account evidence"},
            free_writing="",
            follow_ups=[],
            status=Review.Status.COMPLETED,
        )
        output = valid_report_output()
        output["strengths"][0]["evidence"] = "exclusive other account evidence"
        with patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(output=output),
        ):
            response = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(other.user_id, self.other_user.pk)
        stored = Review.objects.get(pk=review["id"].removeprefix("rev_"))
        self.assertEqual(stored.status, Review.Status.DRAFT)

    def test_regeneration_preserves_user_edits_and_commitment_through_get(self):
        review = self.create_draft()
        initial_output = valid_report_output()
        initial_output["challenges"] = [
            {
                "text": "A challenge from this week.",
                "kind": "observation",
                "evidence": draft_payload()["freeWriting"],
            }
        ]
        with patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(output=initial_output),
        ):
            first = self.client.post(f"/api/reviews/{review['id']}/complete")
        self.assertEqual(first.status_code, 200)
        original = first.json()
        takeaways_edit = {
            "status": "accepted",
            "correction": "This was the key lesson for me.",
        }
        challenges_edit = {"correction": ""}
        for section, insight, patch_data in (
            ("takeaways", original["takeaways"][0], takeaways_edit),
            ("challenges", original["challenges"][0], challenges_edit),
        ):
            changed = self.client.patch(
                f"/api/reviews/{review['id']}/report/{section}/insights/{insight['id']}",
                patch_data,
                format="json",
            )
            self.assertEqual(changed.status_code, 200)
        after_patch = self.client.get(f"/api/reviews/{review['id']}/report").json()
        self.assertEqual(after_patch["takeaways"][0]["status"], "accepted")
        self.assertEqual(after_patch["takeaways"][0]["correction"], takeaways_edit["correction"])
        self.assertEqual(after_patch["challenges"][0]["correction"], "")

        saved_commitment = self.client.put(
            f"/api/reviews/{review['id']}/commitment",
            {"text": "Practice asking early", "measure": "At Monday check-in"},
            format="json",
        )
        self.assertEqual(saved_commitment.status_code, 200)
        commitment_snapshot = saved_commitment.json()

        regenerated_output = {
            "takeaways": [
                {
                    "text": "Changed generated wording for the same lesson.",
                    "kind": "hypothesis",
                    "evidence": draft_payload()["answers"]["learned"],
                }
            ],
            "strengths": [
                {
                    "text": "A newly generated strength.",
                    "kind": "observation",
                    "evidence": draft_payload()["answers"]["wentWell"],
                }
            ],
            "challenges": [],
            "patterns": [],
            "proposedAction": "Take a different small next step.",
        }
        with patch(
            "backend.feedback.reports.get_report_provider",
            return_value=FakeReportProvider(output=regenerated_output),
        ):
            regenerated = self.client.post(f"/api/reviews/{review['id']}/complete")

        self.assertEqual(regenerated.status_code, 200)
        report = self.client.get(f"/api/reviews/{review['id']}/report").json()
        original_takeaway = after_patch["takeaways"][0]
        preserved_takeaways = [
            insight for insight in report["takeaways"]
            if insight["evidence"] == original_takeaway["evidence"]
        ]
        self.assertEqual(len(preserved_takeaways), 1)
        self.assertEqual(
            preserved_takeaways[0],
            {
                key: original_takeaway[key]
                for key in ("id", "text", "kind", "evidence", "status", "correction")
            },
        )
        self.assertEqual(len(report["challenges"]), 1)
        self.assertEqual(
            report["challenges"][0],
            {
                key: after_patch["challenges"][0][key]
                for key in ("id", "text", "kind", "evidence", "status", "correction")
            },
        )
        self.assertEqual(len(report["strengths"]), 1)
        self.assertTrue(report["strengths"][0]["id"].startswith("ins_"))
        self.assertEqual(report["strengths"][0]["status"], "pending")
        self.assertNotEqual(report["strengths"][0]["id"], original["strengths"][0]["id"])
        commitment_after = self.client.get(f"/api/reviews/{review['id']}/commitment").json()
        self.assertEqual(commitment_after, commitment_snapshot)
        self.assertEqual(Commitment.objects.filter(review_id=review["id"].removeprefix("rev_")).count(), 1)
