# Action Pack export (json + markdown), schema id lifeops.actionpack/1.0
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from . import calendar as cal
from .serialize import DISCLAIMER


class PackSource(BaseModel):
    title: str
    source_type: str
    source_name: str = ""
    document_type: str = ""
    language: str = ""
    summary: str = ""


class PackVerification(BaseModel):
    overall_confidence: str
    notes: List[str] = []
    evidence_stats: Dict[str, int] = {}


class PackObligation(BaseModel):
    id: str
    title: str
    owner: Optional[str] = None
    priority: str
    due_at: Optional[str] = None
    confidence: str
    evidence: Optional[str] = None
    evidence_status: str
    needs_verification: bool


class PackTask(BaseModel):
    order: int
    id: str
    title: str
    description: str = ""
    status: str
    due_at: Optional[str] = None
    effort_minutes: Optional[int] = None
    depends_on: List[str] = []
    on_minimum_path: bool = False


class PackDeadline(BaseModel):
    id: str
    label: str
    due_at: Optional[str] = None
    date_text: Optional[str] = None
    kind: str
    status: str
    confidence: str
    needs_verification: bool
    assumed_anchor: bool = False
    evidence: Optional[str] = None
    prerequisite_task_ids: List[str] = []


class PackRequirement(BaseModel):
    item: str
    required: bool
    status: str
    confidence: str
    evidence: Optional[str] = None


class PackRisk(BaseModel):
    description: str
    severity: str
    stated_in_source: bool
    confidence: str
    evidence: Optional[str] = None


class PackQuestion(BaseModel):
    question: str
    reason: str = ""


class PackEvent(BaseModel):
    uid: str
    summary: str
    start: str
    all_day: bool


class ActionPack(BaseModel):
    schema_id: str = "lifeops.actionpack/1.0"
    generated_at: str
    source: PackSource
    verification: PackVerification
    obligations: List[PackObligation]
    deadlines: List[PackDeadline]
    tasks: List[PackTask]
    requirements: List[PackRequirement]
    dependencies: List[Dict[str, str]]
    risks: List[PackRisk]
    unanswered_questions: List[PackQuestion]
    calendar_events: List[PackEvent]
    disclaimer: str = DISCLAIMER


def events_from(data: Dict, deadline_id: Optional[str] = None) -> List[Dict]:
    acts = {a["id"]: a["title"] for a in data["actions"]}
    out = []
    for d in data["deadlines"]:
        if deadline_id and d["id"] != deadline_id:
            continue
        e = cal.event_for_deadline(d, data["title"], [p["title"] for p in d["prerequisites"] if p["status"] != "done"])
        if e:
            out.append(e)
    return out


def build_pack(data: Dict) -> ActionPack:
    deps: Dict[str, List[str]] = {}
    for d in data["dependencies"]:
        deps.setdefault(d["to_action_id"], []).append(d["from_action_id"])
    return ActionPack(
        generated_at=datetime.utcnow().isoformat() + "Z",
        source=PackSource(title=data["title"], source_type=data["source_type"], source_name=data["source_name"],
                          document_type=data["document_type"], language=data["language"], summary=data["summary"]),
        verification=PackVerification(overall_confidence=data["overall_confidence"], notes=data["verification_notes"], evidence_stats=data["verification_stats"]),
        obligations=[PackObligation(**{k: a[k] for k in ("id", "title", "owner", "priority", "due_at", "confidence", "evidence", "evidence_status", "needs_verification")}) for a in data["actions"]],
        deadlines=[PackDeadline(id=d["id"], label=d["label"], due_at=d["due_at"], date_text=d["date_text"], kind=d["kind"], status=d["status"],
                                confidence=d["confidence"], needs_verification=d["needs_verification"], assumed_anchor=d["assumed_anchor"],
                                evidence=d["evidence"], prerequisite_task_ids=[p["action_id"] for p in d["prerequisites"]]) for d in data["deadlines"]],
        tasks=[PackTask(order=n, id=a["id"], title=a["title"], description=a["description"], status=a["status"], due_at=a["due_at"],
                        effort_minutes=a["effort_minutes"], depends_on=deps.get(a["id"], []), on_minimum_path=a["in_minimum_path"])
               for n, a in enumerate(data["actions"], 1)],
        requirements=[PackRequirement(**{k: r[k] for k in ("item", "required", "status", "confidence", "evidence")}) for r in data["requirements"]],
        dependencies=[{"from": d["from_action_id"], "to": d["to_action_id"], "reason": d["reason"]} for d in data["dependencies"]],
        risks=[PackRisk(**{k: r[k] for k in ("description", "severity", "stated_in_source", "confidence", "evidence")}) for r in data["risks"]],
        unanswered_questions=[PackQuestion(question=q["question"], reason=q["reason"]) for q in data["questions"]],
        calendar_events=[PackEvent(uid=e["uid"], summary=e["summary"], start=e["start"], all_day=e["all_day"]) for e in events_from(data)],
    )


def to_markdown(data: Dict) -> str:
    L: List[str] = [f"# {data['title']}", "", f"_Action Pack from LifeOps AI | {data['document_type']} | overall confidence: **{data['overall_confidence']}**_", "", data["summary"], ""]
    if data.get("disclaimer"):
        L += [f"> {data['disclaimer']}", ""]
    L += ["## Deadlines", ""]
    for d in data["deadlines"]:
        when = d["due_at"] or "NEEDS VERIFICATION (no exact date)"
        flag = " (counted from analysis time)" if d["assumed_anchor"] else ""
        L.append(f"- **{d['label']}** - {when} ({d['kind']}){flag}{' (done)' if d['status'] == 'done' else ''}")
        for p in d["prerequisites"]:
            L.append(f"  - needs first: {p['title']}")
    if not data["deadlines"]:
        L.append("_None found._")
    L += ["", "## Checklist (in order)", ""]
    for a in data["actions"]:
        box = "x" if a["status"] == "done" else " "
        extra = f" - due {a['due_at']}" if a["due_at"] else ""
        L.append(f"- [{box}] **{a['title']}**{extra} _(priority {a['priority']}, confidence {a['confidence']})_")
        if a["evidence"]:
            L.append(f"  - source: \"{a['evidence']}\" ({a['evidence_status']})")
    L += ["", "## Requirements", ""]
    L += [f"- {'**required**' if r['required'] else 'optional'}: {r['item']}" for r in data["requirements"]] or ["_None found._"]
    L += ["", "## Risks", ""]
    for r in data["risks"]:
        tag = "stated in source" if r["stated_in_source"] else "INFERENCE - not in source"
        L.append(f"- [{r['severity']}] {r['description']} _({tag})_")
    if not data["risks"]:
        L.append("_None found._")
    L += ["", "## Open questions", ""]
    L += [f"- {q['question']}" + (f" - {q['reason']}" if q["reason"] else "") for q in data["questions"]] or ["_None._"]
    if data["verification_notes"]:
        L += ["", "## Verification notes", ""] + [f"- {n}" for n in data["verification_notes"]]
    L += ["", "---", f"_{DISCLAIMER}_", ""]
    return "\n".join(L)
