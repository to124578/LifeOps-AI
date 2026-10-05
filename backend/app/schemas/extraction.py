# what we ask the model to return
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Conf = Literal["high", "medium", "low"]


def _conf(v):
    v = (str(v) if v is not None else "medium").strip().lower()
    return v if v in ("high", "medium", "low") else "medium"


class _Base(BaseModel):
    model_config = {"extra": "ignore"}


class ActionIn(_Base):
    id: str
    title: str
    description: str = ""
    owner: Optional[str] = None  # who must perform it ("you", "HR team", ...)
    priority: Literal["high", "medium", "low"] = "medium"
    effort_minutes: Optional[int] = None
    due_at: Optional[str] = None  # ISO: YYYY-MM-DD or YYYY-MM-DDTHH:MM; null if unknown
    can_delegate: Optional[bool] = None  # true ONLY if source says someone else may do it
    confidence: Conf = "medium"
    evidence: Optional[str] = None

    _c = field_validator("confidence", mode="before")(_conf)

    @field_validator("priority", mode="before")
    @classmethod
    def _p(cls, v):
        v = (str(v) if v is not None else "medium").strip().lower()
        return v if v in ("high", "medium", "low") else "medium"

    @field_validator("effort_minutes", mode="before")
    @classmethod
    def _e(cls, v):
        try:
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None


class DeadlineIn(_Base):
    id: str
    label: str
    due_at: Optional[str] = None
    date_text: Optional[str] = None  # the date exactly as written in the source
    relative_hours: Optional[float] = None  # e.g. "within 24 hours" -> 24 (when no absolute date)
    kind: Literal["hard", "suggested", "event", "unknown"] = "unknown"
    action_ids: List[str] = Field(default_factory=list)
    confidence: Conf = "medium"
    evidence: Optional[str] = None

    _c = field_validator("confidence", mode="before")(_conf)

    @field_validator("kind", mode="before")
    @classmethod
    def _k(cls, v):
        v = (str(v) if v is not None else "unknown").strip().lower()
        return v if v in ("hard", "suggested", "event", "unknown") else "unknown"


class RequirementIn(_Base):
    item: str
    required: bool = True
    action_ids: List[str] = Field(default_factory=list)
    confidence: Conf = "medium"
    evidence: Optional[str] = None

    _c = field_validator("confidence", mode="before")(_conf)


class RiskIn(_Base):
    description: str
    severity: Literal["high", "medium", "low"] = "medium"
    stated_in_source: bool = True  # false => model's inference, not in the document
    confidence: Conf = "medium"
    evidence: Optional[str] = None

    _c = field_validator("confidence", mode="before")(_conf)

    @field_validator("severity", mode="before")
    @classmethod
    def _s(cls, v):
        v = (str(v) if v is not None else "medium").strip().lower()
        return v if v in ("high", "medium", "low") else "medium"


class QuestionIn(_Base):
    question: str
    reason: str = ""


class Understanding(_Base):
    title: str
    document_type: str = "other"
    language: Optional[str] = None
    summary: str = ""
    sensitive_domains: List[str] = Field(default_factory=list)  # legal|medical|financial|immigration|employment|government
    actions: List[ActionIn] = Field(default_factory=list)
    deadlines: List[DeadlineIn] = Field(default_factory=list)
    requirements: List[RequirementIn] = Field(default_factory=list)
    risks: List[RiskIn] = Field(default_factory=list)
    questions: List[QuestionIn] = Field(default_factory=list)
    confidence: Conf = "medium"
    verification_notes: List[str] = Field(default_factory=list)

    _c = field_validator("confidence", mode="before")(_conf)


class DependencyIn(_Base):
    from_action_id: str  # must be completed first
    to_action_id: str
    reason: str = ""


class SuggestedPrereq(_Base):
    deadline_id: Optional[str] = None
    description: str
    reason: str = ""


class Plan(_Base):
    ordered_action_ids: List[str] = Field(default_factory=list)
    dependencies: List[DependencyIn] = Field(default_factory=list)
    minimum_path: List[str] = Field(default_factory=list)
    suggested_prerequisites: List[SuggestedPrereq] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class WhatIfAI(_Base):
    answer: str
    answerable: bool = True
    quotes: List[str] = Field(default_factory=list)  # verbatim source quotes backing the answer
    verify_with: Optional[str] = None
