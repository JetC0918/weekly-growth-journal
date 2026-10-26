from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic import model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Answers(StrictModel):
    wentWell: str
    didntGoWell: str
    handledBetter: str
    learned: str
    doDifferently: str


class FollowUp(StrictModel):
    question: str
    answer: str


class Attempted(StrEnum):
    yes = "yes"
    partly = "partly"
    no = "no"
    blank = ""


class PreviousActionCheck(StrictModel):
    commitmentId: str
    attempted: Attempted
    whatHappened: str
    learned: str


class SaveReviewInput(StrictModel):
    id: str | None = None
    weekStart: date
    answers: Answers
    freeWriting: str
    followUps: list[FollowUp]
    previousAction: PreviousActionCheck | None = None


class Review(SaveReviewInput):
    id: str
    status: str = Field(pattern="^(draft|completed)$")
    createdAt: datetime
    updatedAt: datetime


class InsightKind(StrEnum):
    observation = "observation"
    hypothesis = "hypothesis"


class InsightStatus(StrEnum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Insight(StrictModel):
    id: str
    text: str
    kind: InsightKind
    evidence: str
    status: InsightStatus
    correction: str | None = None


class ReportSection(StrEnum):
    takeaways = "takeaways"
    strengths = "strengths"
    challenges = "challenges"
    patterns = "patterns"


class Report(StrictModel):
    id: str
    reviewId: str
    takeaways: list[Insight]
    strengths: list[Insight]
    challenges: list[Insight]
    patterns: list[Insight]
    proposedAction: str
    generatedAt: datetime


class InsightPatch(StrictModel):
    status: InsightStatus | None = None
    correction: str | None = None

    @model_validator(mode="after")
    def reject_explicit_null_values(self):
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Insight patch values cannot be null")
        return self


class CommitmentInput(StrictModel):
    text: str = Field(min_length=1)
    measure: str


class Commitment(CommitmentInput):
    id: str
    reviewId: str
    weekStart: date
    createdAt: datetime


class Credentials(StrictModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=200)


class AuthToken(StrictModel):
    accessToken: str
    tokenType: str = "bearer"


class ErrorBody(StrictModel):
    detail: str
