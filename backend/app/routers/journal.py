from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..auth import get_current_user
from ..models import (
    Commitment,
    CommitmentInput,
    Insight,
    InsightKind,
    InsightPatch,
    InsightStatus,
    Report,
    ReportSection,
    Review,
    SaveReviewInput,
)
from ..store import JournalStore, get_store, new_id, utcnow

router = APIRouter(tags=["journal"], dependencies=[Depends(get_current_user)])


def sentences(text: str) -> list[str]:
    import re

    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if len(part.strip()) > 2]


def suggest_follow_ups(review: SaveReviewInput) -> list[str]:
    questions: list[str] = []
    answers = review.answers
    bad = sentences(answers.didntGoWell)
    if bad:
        questions.append(f'Looking at "{bad[0]}" — which part of that was within your control?')
    if len(answers.wentWell.strip()) < 40:
        questions.append("What's one small thing that went well that you might be overlooking?")
    if not answers.learned.strip():
        questions.append("If a friend had lived your week, what would you tell them they learned?")
    plan = answers.doDifferently.strip()
    if plan and not any(token in plan.lower() for token in ("daily", "every", "each", "monday", "tuesday", "morning", "evening")):
        questions.append("How will you know, concretely, that you did this next week?")
    elif not plan:
        questions.append("If you could change just one thing next week, what would it be?")
    return questions[:3]


def make_insight(text: str, kind: InsightKind, evidence: str) -> Insight:
    return Insight(id=new_id("ins"), text=text, kind=kind, evidence=evidence, status=InsightStatus.pending)


def build_report(review: Review, history: list[Review]) -> Report:
    answers = review.answers
    good = sentences(answers.wentWell)
    bad = sentences(answers.didntGoWell)
    learned = sentences(answers.learned)
    takeaways = [make_insight(f"You noticed something about yourself: {learned[0]}", InsightKind.observation, learned[0])] if learned else []
    strengths = [make_insight(f"Something worked: {line}", InsightKind.observation, line) for line in good[:3]]
    challenges = [make_insight(f"A difficulty you named: {line}", InsightKind.observation, line) for line in bad[:2]]
    if good and bad:
        takeaways.append(make_insight("The week included both progress and friction.", InsightKind.observation, f"{good[0]} / {bad[0]}"))
    handled = sentences(answers.handledBetter)
    if handled:
        challenges.append(make_insight("This may be a recurring response under pressure; check whether it appears elsewhere.", InsightKind.hypothesis, handled[0]))
    if review.previousAction and review.previousAction.attempted in ("no", "partly"):
        challenges.append(make_insight("Last week's commitment may have been too big or poorly timed; consider making the next one smaller.", InsightKind.hypothesis, review.previousAction.whatHappened or f"Attempted: {review.previousAction.attempted}"))
    elif review.previousAction and review.previousAction.attempted == "yes":
        strengths.append(make_insight("You followed through on last week's commitment.", InsightKind.observation, review.previousAction.whatHappened or "Attempted: yes"))
    patterns: list[Insight] = []
    words = set((" ".join([*answers.model_dump().values(), review.freeWriting] + [f.answer for f in review.followUps])).lower().split())
    past = [item for item in history if item.id != review.id and item.status == "completed"]
    for word in sorted(w for w in words if len(w) >= 6):
        matched = [item.weekStart.isoformat() for item in past if word in " ".join(item.answers.model_dump().values()).lower()]
        if matched:
            patterns.append(make_insight(f'"{word}" appears in multiple reviews. This might be a recurring theme — or a coincidence.', InsightKind.hypothesis, f"Also mentioned in weeks of {', '.join(matched)}"))
        if len(patterns) == 3:
            break
    plan = sentences(answers.doDifferently)
    proposed_action = plan[0] if plan else (f'Pick one specific moment this week to respond differently to: "{bad[0]}"' if bad else "")
    return Report(id=new_id("rep"), reviewId=review.id, takeaways=takeaways, strengths=strengths, challenges=challenges, patterns=patterns, proposedAction=proposed_action, generatedAt=utcnow())


@router.get("/reviews", response_model=list[Review])
def list_reviews(user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    return sorted(store.reviews[user.id].values(), key=lambda review: review.weekStart, reverse=True)


@router.post("/reviews", response_model=Review, status_code=status.HTTP_201_CREATED)
def save_review(payload: SaveReviewInput, response: Response, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    reviews = store.reviews[user.id]
    existing = reviews.get(payload.id) if payload.id else None
    if existing is None:
        existing = next((review for review in reviews.values() if review.weekStart == payload.weekStart), None)
    now = utcnow()
    if existing:
        data = payload.model_dump(exclude={"id"})
        updated = Review.model_validate({**existing.model_dump(), **data, "updatedAt": now})
        reviews[updated.id] = updated
        response.status_code = status.HTTP_200_OK
        return updated
    created = Review(**payload.model_dump(exclude={"id"}), id=new_id("rev"), status="draft", createdAt=now, updatedAt=now)
    reviews[created.id] = created
    return created


@router.get("/reviews/by-week/{weekStart}", response_model=Review | None)
def get_review_for_week(weekStart: date, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    return next((review for review in store.reviews[user.id].values() if review.weekStart == weekStart), None)


@router.get("/reviews/{reviewId}", response_model=Review | None)
def get_review(reviewId: str, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    return store.reviews[user.id].get(reviewId)


@router.delete("/reviews/{reviewId}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(reviewId: str, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    store.reviews[user.id].pop(reviewId, None)
    store.reports[user.id].pop(reviewId, None)
    store.commitments[user.id].pop(reviewId, None)


@router.post("/reviews/suggest-follow-ups", response_model=list[str])
def follow_up_suggestions(payload: SaveReviewInput, user=Depends(get_current_user)):
    return suggest_follow_ups(payload)


@router.post("/reviews/{reviewId}/complete", response_model=Report)
def complete_review(reviewId: str, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    review = store.reviews[user.id].get(reviewId)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    completed = Review.model_validate({**review.model_dump(), "status": "completed", "updatedAt": utcnow()})
    store.reviews[user.id][reviewId] = completed
    report = build_report(completed, list(store.reviews[user.id].values()))
    store.reports[user.id][reviewId] = report
    return report


@router.get("/reviews/{reviewId}/report", response_model=Report | None)
def get_report(reviewId: str, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    return store.reports[user.id].get(reviewId)


@router.patch("/reviews/{reviewId}/report/{section}/insights/{insightId}", response_model=Report)
def update_insight(reviewId: str, section: ReportSection, insightId: str, patch: InsightPatch, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    report = store.reports[user.id].get(reviewId)
    insight = next((item for item in getattr(report, section.value, []) if item.id == insightId), None) if report else None
    changes = patch.model_dump(exclude_unset=True)
    if report is None or insight is None or not changes:
        raise HTTPException(status_code=404 if report is None or insight is None else 400, detail="Insight not found" if report is None or insight is None else "At least one field is required")
    updated_insight = insight.model_copy(update=changes)
    updated_section = [updated_insight if item.id == insightId else item for item in getattr(report, section.value)]
    updated_report = report.model_copy(update={section.value: updated_section})
    store.reports[user.id][reviewId] = updated_report
    return updated_report


@router.get("/reviews/{reviewId}/commitment", response_model=Commitment | None)
def get_commitment(reviewId: str, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    return store.commitments[user.id].get(reviewId)


@router.put("/reviews/{reviewId}/commitment", response_model=Commitment)
def set_commitment(reviewId: str, payload: CommitmentInput, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    review = store.reviews[user.id].get(reviewId)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    existing = store.commitments[user.id].get(reviewId)
    commitment = Commitment(
        id=existing.id if existing else new_id("com"),
        reviewId=reviewId,
        weekStart=review.weekStart,
        text=payload.text.strip(),
        measure=payload.measure.strip(),
        createdAt=existing.createdAt if existing else utcnow(),
    )
    if not commitment.text:
        raise HTTPException(status_code=400, detail="Commitment cannot be empty")
    store.commitments[user.id][reviewId] = commitment
    return commitment


@router.get("/commitments/before", response_model=Commitment | None)
def commitment_before(weekStart: date, user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    commitments = [item for item in store.commitments[user.id].values() if item.weekStart < weekStart]
    return max(commitments, key=lambda item: item.weekStart, default=None)


@router.delete("/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_data(user=Depends(get_current_user), store: JournalStore = Depends(get_store)):
    store.reviews[user.id].clear()
    store.reports[user.id].clear()
    store.commitments[user.id].clear()
