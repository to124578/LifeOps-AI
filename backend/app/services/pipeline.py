# runs the pipeline in the background and saves after each stage so the UI can poll
import json
import time
import uuid
from datetime import datetime
from typing import Optional

from ..core.db import SessionLocal
from ..core.errors import AppError
from ..models.db_models import Action, Analysis, Deadline, Dependency, Question, Requirement, Risk
from . import calendar as cal
from .agents import intake, planning, understanding, verification
from .ai_provider import get_provider
from .serialize import serialize_analysis

STAGES = ["intake", "understanding", "planning", "verification", "action"]


class _Trace:
    def __init__(self, db, a: Analysis):
        self.db, self.a, self.items = db, a, []

    def start(self, name: str, label: str):
        self.items.append({"name": name, "label": label, "status": "running", "ms": 0, "summary": ""})
        self.a.stage = name
        self._save()
        self._t = time.time()

    def finish(self, summary: str, status: str = "done"):
        it = self.items[-1]
        it.update(status=status, ms=int((time.time() - self._t) * 1000), summary=summary)
        self._save()

    def fail(self, summary: str):
        if self.items:
            self.items[-1].update(status="failed", summary=summary, ms=int((time.time() - self._t) * 1000))
        self._save()

    def _save(self):
        self.a.pipeline_json = json.dumps(self.items)
        self.db.commit()


def run_pipeline(analysis_id: str, text: Optional[str], upload: Optional[intake.UploadPayload], anchor: Optional[str]):
    db = SessionLocal()
    try:
        a = db.get(Analysis, analysis_id)
        if a is None:
            return
        tr = _Trace(db, a)
        extras = {}
        try:
            from ..core.config import get_settings
            s = get_settings()
            provider = get_provider(s)
            extras["provider"] = f"{provider.name}:{s.model}"
            today = (a.client_now or datetime.utcnow().isoformat())[:10]

            tr.start("intake", "Intake Agent")
            ir = intake.run(text, upload, provider, s.max_input_chars)
            a.raw_text, a.source_type, a.language = ir.raw_text, ir.source_type, ir.language
            extras["intake_notes"] = ir.notes
            tr.finish(f"{ir.source_type.upper()} | {len(ir.raw_text):,} chars | language {ir.language} | looks like: {ir.doc_type_hint}")

            tr.start("understanding", "Understanding Agent")
            u = understanding.run(provider, ir.raw_text, today, a.client_now or today)
            tr.finish(f"{len(u.actions)} actions | {len(u.deadlines)} deadlines | {len(u.requirements)} requirements | {len(u.risks)} risks")

            tr.start("planning", "Planning Agent")
            plan, degraded = planning.run(provider, u, ir.raw_text, today)
            tr.finish(f"{len(plan.dependencies)} dependencies | minimum path of {len(plan.minimum_path)} steps" + (" (fallback ordering)" if degraded else ""),
                      "degraded" if degraded else "done")

            tr.start("verification", "Verification Agent")
            v = verification.run(u, plan, ir.raw_text, a.client_now or datetime.utcnow().isoformat(), anchor, degraded)
            st = v["stats"]
            tr.finish(f"{st['verified']} quotes verified | {st['partial']} partial | {st['unsupported'] + st['none']} need verification")

            _persist(db, a, u, v, extras)

            tr.start("action", "Action Agent")
            ser = serialize_analysis(db, a, include_raw=False)
            events = [e for e in (cal.event_for_deadline(d, a.title) for d in ser["deadlines"]) if e]
            cal.build_ics(events)  # make sure ics generation doesn't blow up
            tr.finish(f"{len(ser['actions'])} checklist items | {len(events)} calendar events | Action Pack ready")
            a.status, a.stage, a.error = "done", "done", None
        except AppError as e:
            db.rollback()
            a = db.get(Analysis, analysis_id)
            tr.a = a
            tr.fail(e.message)
            a.status, a.error = "failed", e.message
        except Exception:
            db.rollback()
            a = db.get(Analysis, analysis_id)
            tr.a = a
            msg = "Something went wrong while analyzing. Please try again."
            tr.fail(msg)
            a.status, a.error = "failed", msg
        a.extras_json = json.dumps({**json.loads(a.extras_json or "{}"), **extras})
        db.commit()
    finally:
        db.close()


def _persist(db, a: Analysis, u, v, extras):
    a.title = u.title[:200]
    a.document_type = u.document_type
    a.summary = u.summary
    a.overall_confidence = v["overall_confidence"]
    extras.update(notes=v["notes"], stats=v["stats"], sensitive_domains=v["sensitive_domains"],
                  minimum_path=v["minimum_path"], suggested_prerequisites=v["suggested_prerequisites"])
    a.extras_json = json.dumps(extras)
    key2id = {}
    for x in v["actions"]:
        row = Action(id=uuid.uuid4().hex, analysis_id=a.id, key=x["id"], title=x["title"], description=x["description"], owner=x["owner"],
                     priority=x["priority"], due_at=x["due_at"], confidence=x["confidence"], evidence=x["evidence"],
                     evidence_status=x["evidence_status"], effort_minutes=x["effort_minutes"], can_delegate=x["can_delegate"],
                     needs_verification=x["needs_verification"], order_index=x["order_index"])
        db.add(row)
        key2id[x["id"]] = row.id
    for d in v["deadlines"]:
        db.add(Deadline(analysis_id=a.id, key=d["id"], label=d["label"], due_at=d["due_at"], date_text=d["date_text"], kind=d["kind"],
                        confidence=d["confidence"], evidence=d["evidence"], evidence_status=d["evidence_status"],
                        needs_verification=d["needs_verification"], assumed_anchor=d["assumed_anchor"], action_keys=json.dumps(d["action_ids"])))
    for r in v["requirements"]:
        db.add(Requirement(analysis_id=a.id, item=r["item"], required=r["required"], confidence=r["confidence"], evidence=r["evidence"],
                           evidence_status=r["evidence_status"], action_keys=json.dumps(r["action_ids"])))
    for d in v["dependencies"]:
        db.add(Dependency(analysis_id=a.id, from_action_id=key2id[d["from_action_id"]], to_action_id=key2id[d["to_action_id"]], reason=d["reason"]))
    for r in v["risks"]:
        db.add(Risk(analysis_id=a.id, description=r["description"], severity=r["severity"], stated_in_source=r["stated_in_source"],
                    confidence=r["confidence"], evidence=r["evidence"], evidence_status=r["evidence_status"]))
    for q in v["questions"]:
        db.add(Question(analysis_id=a.id, question=q["question"], reason=q["reason"]))
    db.commit()
