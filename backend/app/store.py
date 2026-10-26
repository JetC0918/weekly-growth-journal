import os
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import Request

from .models import (
    Answers,
    Commitment,
    FollowUp,
    Insight,
    InsightKind,
    InsightStatus,
    PreviousActionCheck,
    Report,
    Review,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class UserRecord:
    def __init__(self, username: str, password_salt: str, password_hash: str, user_id: str | None = None):
        self.id = user_id or new_id("usr")
        self.username = username
        self.password_salt = password_salt
        self.password_hash = password_hash


class JournalStore:
    """Simple process-local store. Data is separated by authenticated user id."""

    def __init__(self):
        self.users: dict[str, UserRecord] = {}
        self.usernames: dict[str, str] = {}
        self.reviews: dict[str, dict[str, Review]] = {}
        self.reports: dict[str, dict[str, Report]] = {}
        self.commitments: dict[str, dict[str, Commitment]] = {}

    def add_user(self, user: UserRecord) -> None:
        self.users[user.id] = user
        self.usernames[user.username.casefold()] = user.id
        self.reviews[user.id] = {}
        self.reports[user.id] = {}
        self.commitments[user.id] = {}

    def user_by_username(self, username: str) -> UserRecord | None:
        user_id = self.usernames.get(username.casefold())
        return self.users.get(user_id) if user_id else None

    def seed_demo_data(self, user_id: str) -> None:
        now = utcnow()
        current_week = date.today() - timedelta(days=date.today().weekday())
        previous_week = current_week - timedelta(days=7)
        answers = Answers(
            wentWell="I protected focused time for a project and finished the first draft.",
            didntGoWell="I postponed a difficult conversation until Friday.",
            handledBetter="I could have raised the blocker as soon as I noticed it.",
            learned="I do better when I make the first step small and visible.",
            doDifferently="I will flag blockers in the team check-in on Tuesday.",
        )
        past = Review(
            id=new_id("rev"),
            weekStart=previous_week,
            answers=answers,
            freeWriting="The project moved forward once I asked for input.",
            followUps=[FollowUp(question="What helped?", answer="A clear first step." )],
            previousAction=None,
            status="completed",
            createdAt=now - timedelta(days=7),
            updatedAt=now - timedelta(days=6),
        )
        past_commitment = Commitment(
            id=new_id("com"),
            reviewId=past.id,
            weekStart=past.weekStart,
            text="Ask for input early",
            measure="Mention it in the weekly check-in",
            createdAt=now - timedelta(days=7),
        )
        current = Review(
            id=new_id("rev"),
            weekStart=current_week,
            answers=answers,
            freeWriting="I want to keep making progress without waiting for perfect conditions.",
            followUps=[],
            previousAction=PreviousActionCheck(
                commitmentId=past_commitment.id,
                attempted="partly",
                whatHappened="I raised one blocker, but only near the end of the week.",
                learned="I need to make the check-in reminder visible.",
            ),
            status="completed",
            createdAt=now,
            updatedAt=now,
        )
        self.reviews[user_id][past.id] = past
        self.reviews[user_id][current.id] = current
        for review, label in ((past, "Ask for input early"), (current, "Raise blockers at Tuesday check-in")):
            insight = Insight(
                id=new_id("ins"),
                text=f"You made progress by taking a small first step: {label}.",
                kind=InsightKind.observation,
                evidence=review.answers.learned,
                status=InsightStatus.pending,
            )
            self.reports[user_id][review.id] = Report(
                id=new_id("rep"),
                reviewId=review.id,
                takeaways=[insight],
                strengths=[],
                challenges=[],
                patterns=[],
                proposedAction=label,
                generatedAt=now,
            )
            commitment = past_commitment if review.id == past.id else Commitment(
                id=new_id("com"),
                reviewId=review.id,
                weekStart=review.weekStart,
                text=label,
                measure="Mention it in the weekly check-in",
                createdAt=now,
            )
            self.commitments[user_id][review.id] = commitment


def get_store(request: Request) -> JournalStore:
    return request.app.state.store


def create_seeded_store() -> tuple[JournalStore, str, str]:
    from .auth import hash_password

    store = JournalStore()
    username = os.getenv("DEMO_USERNAME", "demo")
    password = os.getenv("DEMO_PASSWORD", "journal-demo")
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    user = UserRecord(username, salt, password_hash)
    store.add_user(user)
    store.seed_demo_data(user.id)
    return store, username, password

