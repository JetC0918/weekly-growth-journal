"""OpenAI-compatible follow-up question generation for journal drafts."""

import json
from typing import Any, Callable, Mapping, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings


class FollowUpProviderError(Exception):
    """A provider failure with a safe message suitable for API responses."""

    status_code = 502
    detail = "Follow-up suggestions are temporarily unavailable. Please try again later."

    def __init__(self):
        super().__init__(self.detail)


class ProviderNotConfigured(FollowUpProviderError):
    status_code = 503
    detail = "Follow-up suggestions are unavailable until an AI provider is configured."


class ReportProviderError(Exception):
    status_code = 502
    detail = "Feedback report generation is temporarily unavailable. Please try again later."

    def __init__(self):
        super().__init__(self.detail)


class ReportProviderNotConfigured(ReportProviderError):
    status_code = 503
    detail = "Report generation is unavailable until an AI provider is configured."


class DeterministicFakeProvider:
    """Predictable local provider that only cites text supplied in the review context."""

    def suggest_questions(self, draft: Mapping[str, Any]) -> list[str]:
        if not _has_reflection_content(draft):
            return []
        return [
            "What is one small step you want to try next week?",
            "What could make that step easier to start?",
        ]

    def generate_report(self, report_context: Mapping[str, Any]) -> dict[str, Any]:
        current = report_context["currentReview"]
        history = report_context.get("earlierReviews", [])
        evidence = _first_nonblank_evidence([current, *history])
        strengths_evidence = current["answers"].get("wentWell", "")
        if not isinstance(strengths_evidence, str) or not strengths_evidence.strip():
            strengths_evidence = ""
        challenges_evidence = current["answers"].get("didntGoWell", "").strip()

        def insight(text: str, exact_evidence: str) -> dict[str, str]:
            return {
                "text": text,
                "kind": "observation",
                "evidence": exact_evidence,
            }

        return {
            "takeaways": [insight("You recorded a concrete detail from your reflection.", evidence)],
            "strengths": [
                insight("You identified something that went well.", strengths_evidence)
            ] if strengths_evidence else [],
            "challenges": [
                insight("You identified something that did not go as planned.", challenges_evidence)
            ] if challenges_evidence else [],
            "patterns": [],
            "proposedAction": "Choose one small next step from this reflection.",
        }


def _first_nonblank_evidence(reviews: list[Mapping[str, Any]]) -> str:
    for review in reviews:
        for answer in review.get("answers", {}).values():
            if isinstance(answer, str) and answer.strip():
                return answer
        free_writing = review.get("freeWriting", "")
        if isinstance(free_writing, str) and free_writing.strip():
            return free_writing
        for follow_up in review.get("followUps", []):
            for value in (follow_up.get("answer", ""), follow_up.get("question", "")):
                if isinstance(value, str) and value.strip():
                    return value
    return ""


class _ProviderCallError(Exception):
    pass


class FollowUpProvider(Protocol):
    def suggest_questions(self, draft: Mapping[str, Any]) -> list[str]: ...


class ReportProvider(Protocol):
    def generate_report(self, report_context: Mapping[str, Any]) -> dict[str, Any]: ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: float = 15,
        opener: Callable[..., Any] | None = None,
    ):
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds
        self.opener = opener or urlopen

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model and self.api_key)

    def suggest_questions(self, draft: Mapping[str, Any]) -> list[str]:
        if not self.is_configured():
            raise ProviderNotConfigured()

        user_content = {
            "answers": draft["answers"],
            "freeWriting": draft["freeWriting"],
            "followUps": draft["followUps"],
            "previousAction": draft.get("previousAction"),
        }
        try:
            content = self._request_completion(
                "Suggest up to three concise follow-up questions grounded in the reflection. "
                'Return only a JSON object with a "questions" array of strings.',
                user_content,
            )
            parsed_content = json.loads(content)
            questions = parsed_content["questions"]
            if not isinstance(questions, list) or not all(isinstance(question, str) for question in questions):
                raise ValueError("questions must be an array of strings")
        except Exception:
            # Provider payloads and exception text may contain journal content or credentials.
            raise FollowUpProviderError() from None

        usable = [
            question.strip()
            for question in questions
            if question.strip() and len(question.strip()) <= 200
        ][:3]
        if not usable:
            raise FollowUpProviderError()
        return usable

    def generate_report(self, report_context: Mapping[str, Any]) -> dict[str, Any]:
        if not self.is_configured():
            raise ReportProviderNotConfigured()

        system_prompt = (
            "Generate an evidence-grounded weekly reflection report. Return only a JSON object with "
            'exactly these fields: "takeaways", "strengths", "challenges", "patterns", and '
            '"proposedAction". Each insight must have only "text", "kind" (observation or hypothesis), '
            'and "evidence". Evidence must be copied exactly from the current review or supplied history. '
            "Do not include ids, statuses, timestamps, corrections, or any other fields."
        )
        try:
            content = self._request_completion(system_prompt, report_context)
            parsed_content = json.loads(content)
            if not isinstance(parsed_content, dict):
                raise ValueError("report must be an object")
            return parsed_content
        except Exception:
            raise ReportProviderError() from None

    def _request_completion(self, system_prompt: str, user_content: Mapping[str, Any]) -> str:
        endpoint = (
            self.base_url
            if self.base_url.endswith("/chat/completions")
            else f"{self.base_url}/chat/completions"
        )
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }
        request = Request(
            endpoint,
            data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                provider_response = json.loads(response.read().decode("utf-8"))
            content = provider_response["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("completion content must be text")
            return content
        except HTTPError as error:
            error.close()
            raise _ProviderCallError() from None
        except Exception:
            raise _ProviderCallError() from None


def get_follow_up_provider() -> FollowUpProvider:
    if settings.AI_PROVIDER_MODE == "fake":
        if not settings.DEBUG:
            raise ProviderNotConfigured()
        return DeterministicFakeProvider()
    if settings.AI_PROVIDER_MODE != "openai":
        raise ProviderNotConfigured()
    return OpenAICompatibleProvider(
        base_url=settings.AI_BASE_URL,
        model=settings.AI_MODEL,
        api_key=settings.AI_API_KEY,
    )


def get_report_provider() -> ReportProvider:
    if settings.AI_PROVIDER_MODE == "fake":
        if not settings.DEBUG:
            raise ReportProviderNotConfigured()
        return DeterministicFakeProvider()
    if settings.AI_PROVIDER_MODE != "openai":
        raise ReportProviderNotConfigured()
    return OpenAICompatibleProvider(
        base_url=settings.AI_BASE_URL,
        model=settings.AI_MODEL,
        api_key=settings.AI_API_KEY,
    )


def _has_reflection_content(draft: Mapping[str, Any]) -> bool:
    free_writing = draft.get("free_writing", draft.get("freeWriting", ""))
    follow_ups = draft.get("follow_ups", draft.get("followUps", []))
    values = [*draft["answers"].values(), free_writing]
    values.extend(item["answer"] for item in follow_ups)
    return any(value.strip() for value in values)


def _provider_draft(draft: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "answers": draft["answers"],
        "freeWriting": draft.get("free_writing", draft.get("freeWriting", "")),
        "followUps": draft.get("follow_ups", draft.get("followUps", [])),
        "previousAction": draft.get("previous_action", draft.get("previousAction")),
    }


def suggest_follow_up_questions(
    draft: Mapping[str, Any], provider: FollowUpProvider | None = None
) -> list[str]:
    if not _has_reflection_content(draft):
        return []
    return (provider or get_follow_up_provider()).suggest_questions(_provider_draft(draft))
