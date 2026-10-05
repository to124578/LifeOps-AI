import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from ..core.db import Base


def _id() -> str:
    return uuid.uuid4().hex


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=_id)
    session_id = Column(String, index=True, nullable=False)
    title = Column(String, default="Untitled")
    source_type = Column(String, default="text")  # text | txt | pdf | image
    source_name = Column(String, default="")
    raw_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    client_now = Column(String, default="")  # user's local "now", ISO, no tz
    language = Column(String, default="")
    status = Column(String, default="processing")  # processing | done | failed
    stage = Column(String, default="queued")
    error = Column(Text, nullable=True)
    document_type = Column(String, default="")
    summary = Column(Text, default="")
    overall_confidence = Column(String, default="")
    pipeline_json = Column(Text, default="[]")
    extras_json = Column(Text, default="{}")  # minimum_path, notes, suggested prereqs, domains


class Action(Base):
    __tablename__ = "actions"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    key = Column(String, default="")
    title = Column(String, default="")
    description = Column(Text, default="")
    owner = Column(String, nullable=True)
    priority = Column(String, default="medium")
    status = Column(String, default="todo")  # todo | done
    due_at = Column(String, nullable=True)
    confidence = Column(String, default="medium")
    evidence = Column(Text, nullable=True)
    evidence_status = Column(String, default="none")  # verified | partial | unsupported | none
    effort_minutes = Column(Integer, nullable=True)
    can_delegate = Column(Boolean, nullable=True)
    needs_verification = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)


class Deadline(Base):
    __tablename__ = "deadlines"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    key = Column(String, default="")
    label = Column(String, default="")
    due_at = Column(String, nullable=True)
    date_text = Column(String, nullable=True)
    kind = Column(String, default="unknown")  # hard | suggested | event | unknown
    confidence = Column(String, default="medium")
    evidence = Column(Text, nullable=True)
    evidence_status = Column(String, default="none")
    needs_verification = Column(Boolean, default=False)
    assumed_anchor = Column(Boolean, default=False)
    status = Column(String, default="open")  # open | done
    action_keys = Column(Text, default="[]")


class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    item = Column(Text, default="")
    required = Column(Boolean, default=True)
    status = Column(String, default="missing")  # missing | have
    confidence = Column(String, default="medium")
    evidence = Column(Text, nullable=True)
    evidence_status = Column(String, default="none")
    action_keys = Column(Text, default="[]")


class Dependency(Base):
    __tablename__ = "dependencies"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    from_action_id = Column(String, nullable=False)  # must be done first
    to_action_id = Column(String, nullable=False)
    reason = Column(Text, default="")


class Risk(Base):
    __tablename__ = "risks"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    description = Column(Text, default="")
    severity = Column(String, default="medium")
    stated_in_source = Column(Boolean, default=True)
    confidence = Column(String, default="medium")
    evidence = Column(Text, nullable=True)
    evidence_status = Column(String, default="none")


class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=_id)
    analysis_id = Column(String, index=True, nullable=False)
    question = Column(Text, default="")
    reason = Column(Text, default="")


ANALYSIS_CHILD_TABLES = [Action, Deadline, Requirement, Dependency, Risk, Question]
