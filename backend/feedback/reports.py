"""Report context preparation, provider output validation, and persistence data."""

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from django.utils import timezone

from .follow_ups import ReportProvider, ReportProviderError, get_report_provider

REPORT_SECTIONS = ("takeaways", "strengths", "challenges", "patterns")
REPORT_FIELDS = {*REPORT_SECTIONS, "proposedAction"}
INSIGHT_FIELDS = {"text", "kind", "evidence"}
INSIGHT_KINDS = {"observation", "hypothesis"}


class InsufficientReflectionContent(Exception):
    detail = "Add at least one reflection answer, free-writing entry, or follow-up answer before completing a review."


def _value(item: Any, public_name: str, model_name: str | None = None, default=None):
    model_name = model_name or public_name
    if isinstance(item, Mapping):
        return item.get(model_name, item.get(public_name, default))
    return getattr(item, model_name, default)


def serialize_review_context(review: Any) -> dict[str, Any]:
    week_start = _value(review, "weekStart", "week_start")
    if hasattr(week_start, "isoformat"):
        week_start = week_start.isoformat()
    previous_action = _value(review, "previousAction", "previous_action")
    if previous_action:
        previous_action = {
            "attempted": previous_action.get("attempted", ""),
            "whatHappened": previous_action.get("whatHappened", ""),
            "learned": previous_action.get("learned", ""),
        }
    return {
        "weekStart": week_start,
        "answers": _value(review, "answers", default={}),
        "freeWriting": _value(review, "freeWriting", "free_writing", ""),
        "followUps": _value(review, "followUps", "follow_ups", []),
        "previousAction": previous_action,
    }


def _has_review_content(review: Mapping[str, Any]) -> bool:
    values = [*review["answers"].values(), review["freeWriting"]]
    values.extend(item["answer"] for item in review["followUps"])
    return any(isinstance(value, str) and value.strip() for value in values)


def _evidence_sources(reviews: list[Mapping[str, Any]]) -> list[str]:
    sources: list[str] = []
    for review in reviews:
        sources.extend(value for value in review["answers"].values() if isinstance(value, str))
        sources.append(review["freeWriting"])
        for follow_up in review["followUps"]:
            sources.extend((follow_up["question"], follow_up["answer"]))
        previous = review.get("previousAction")
        if previous:
            sources.extend((previous["whatHappened"], previous["learned"]))
    return [source for source in sources if isinstance(source, str)]


def _validate_provider_report(
    output: Any,
    current_review: Mapping[str, Any],
    history: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if not isinstance(output, dict) or set(output) != REPORT_FIELDS:
        raise ReportProviderError()

    evidence_sources = _evidence_sources([current_review, *history])
    normalized_sections = {}
    for section in REPORT_SECTIONS:
        insights = output[section]
        if not isinstance(insights, list):
            raise ReportProviderError()
        normalized = []
        for insight in insights:
            if not isinstance(insight, dict) or set(insight) != INSIGHT_FIELDS:
                raise ReportProviderError()
            text = insight["text"]
            kind = insight["kind"]
            evidence = insight["evidence"]
            if (
                not isinstance(text, str)
                or not text.strip()
                or not isinstance(kind, str)
                or kind not in INSIGHT_KINDS
                or not isinstance(evidence, str)
                or not evidence.strip()
                or not any(evidence in source for source in evidence_sources)
            ):
                raise ReportProviderError()
            normalized.append(
                {
                    "id": f"ins_{uuid4().hex}",
                    "text": text.strip(),
                    "kind": kind,
                    "evidence": evidence,
                    "status": "pending",
                }
            )
        normalized_sections[section] = normalized

    proposed_action = output["proposedAction"]
    if not isinstance(proposed_action, str):
        raise ReportProviderError()
    return {
        **normalized_sections,
        "proposed_action": proposed_action.strip(),
        "generated_at": timezone.now(),
    }


def generate_report_data(
    review: Any,
    history: list[Any],
    provider: ReportProvider | None = None,
) -> dict[str, Any]:
    current_context = serialize_review_context(review)
    history_context = [serialize_review_context(item) for item in history[:5]]
    if not _has_review_content(current_context):
        raise InsufficientReflectionContent()

    context = {"currentReview": current_context, "earlierReviews": history_context}
    raw_report = (provider or get_report_provider()).generate_report(context)
    return _validate_provider_report(raw_report, current_context, history_context)


def merge_user_edits(existing_report: Any | None, generated_data: dict[str, Any]) -> dict[str, Any]:
    """Keep edited insights while replacing the report's generated content."""
    if existing_report is None:
        return generated_data

    merged = dict(generated_data)
    for section in REPORT_SECTIONS:
        existing = getattr(existing_report, section)
        edited = [
            dict(insight)
            for insight in existing
            if insight.get("status", "pending") != "pending" or "correction" in insight
        ]
        edited_by_evidence: dict[str, list[dict[str, Any]]] = {}
        for insight in edited:
            evidence = insight.get("evidence")
            if isinstance(evidence, str):
                edited_by_evidence.setdefault(evidence, []).append(insight)

        output = []
        seen_generated_evidence: set[str] = set()
        matched_edits: set[int] = set()
        for insight in generated_data[section]:
            evidence = insight["evidence"]
            if evidence in seen_generated_evidence:
                continue
            seen_generated_evidence.add(evidence)
            matches = edited_by_evidence.get(evidence, [])
            if matches:
                preserved = matches[0]
                output.append(preserved)
                matched_edits.add(id(preserved))
            else:
                output.append(insight)

        output.extend(insight for insight in edited if id(insight) not in matched_edits)
        merged[section] = output
    return merged
