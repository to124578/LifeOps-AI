import json
from typing import Dict, List

from sqlalchemy.orm import Session

from ..models.db_models import Action, Analysis, Deadline, Dependency, Question, Requirement, Risk

DISCLAIMER = (
    "LifeOps AI organises information to help you act. It is not legal, medical, financial, immigration, "
    "employment or government advice. Verify important details with the original sender or a qualified professional."
)


def _j(s, default):
    try:
        return json.loads(s) if s else default
    except ValueError:
        return default


def serialize_analysis(db: Session, a: Analysis, include_raw: bool = True) -> Dict:
    actions = db.query(Action).filter_by(analysis_id=a.id).order_by(Action.order_index).all()
    deadlines = db.query(Deadline).filter_by(analysis_id=a.id).all()
    reqs = db.query(Requirement).filter_by(analysis_id=a.id).all()
    deps = db.query(Dependency).filter_by(analysis_id=a.id).all()
    risks = db.query(Risk).filter_by(analysis_id=a.id).all()
    qs = db.query(Question).filter_by(analysis_id=a.id).all()
    extras = _j(a.extras_json, {})
    key2id = {x.key: x.id for x in actions}
    by_id = {x.id: x for x in actions}
    min_path = [key2id[k] for k in extras.get("minimum_path", []) if k in key2id]

    preds: Dict[str, set] = {}
    for d in deps:
        preds.setdefault(d.to_action_id, set()).add(d.from_action_id)

    def all_preds(ids) -> set:
        out, stack = set(), list(ids)
        while stack:
            n = stack.pop()
            for p in preds.get(n, ()):
                if p not in out:
                    out.add(p)
                    stack.append(p)
        return out

    req_out = []
    for r in reqs:
        req_out.append({
            "id": r.id, "item": r.item, "required": r.required, "status": r.status, "confidence": r.confidence,
            "evidence": r.evidence, "evidence_status": r.evidence_status,
            "action_ids": [key2id[k] for k in _j(r.action_keys, []) if k in key2id],
        })

    dl_out: List[Dict] = []
    for d in sorted(deadlines, key=lambda x: (x.due_at or "9999", x.key)):
        linked = [key2id[k] for k in _j(d.action_keys, []) if k in key2id]
        pre = all_preds(linked)
        pre_list = [{"action_id": p, "title": by_id[p].title, "status": by_id[p].status} for p in pre if p in by_id]
        scope = set(linked) | pre
        unmet = [{"id": r["id"], "item": r["item"]} for r in req_out if r["required"] and r["status"] != "have" and set(r["action_ids"]) & scope]
        done = d.status == "done" or (bool(linked) and all(by_id[i].status == "done" for i in linked))
        dl_out.append({
            "id": d.id, "key": d.key, "label": d.label, "due_at": d.due_at, "date_text": d.date_text, "kind": d.kind,
            "confidence": d.confidence, "evidence": d.evidence, "evidence_status": d.evidence_status,
            "needs_verification": d.needs_verification, "assumed_anchor": d.assumed_anchor,
            "status": "done" if done else "open", "action_ids": linked,
            "prerequisites": pre_list, "unmet_requirements": unmet,
            "suggested_prerequisites": [s for s in extras.get("suggested_prerequisites", []) if s.get("deadline_id") == d.key],
        })

    out = {
        "id": a.id, "title": a.title, "source_type": a.source_type, "source_name": a.source_name,
        "document_type": a.document_type, "language": a.language, "summary": a.summary,
        "status": a.status, "stage": a.stage, "error": a.error,
        "created_at": a.created_at.isoformat() + "Z" if a.created_at else None,
        "overall_confidence": a.overall_confidence, "verification_notes": extras.get("notes", []),
        "verification_stats": extras.get("stats", {}), "intake_notes": extras.get("intake_notes", []),
        "sensitive_domains": extras.get("sensitive_domains", []),
        "disclaimer": DISCLAIMER if extras.get("sensitive_domains") else None,
        "provider": extras.get("provider", ""), "pipeline": _j(a.pipeline_json, []),
        "actions": [{
            "id": x.id, "key": x.key, "title": x.title, "description": x.description, "owner": x.owner,
            "priority": x.priority, "status": x.status, "due_at": x.due_at, "confidence": x.confidence,
            "evidence": x.evidence, "evidence_status": x.evidence_status, "effort_minutes": x.effort_minutes,
            "can_delegate": x.can_delegate, "needs_verification": x.needs_verification, "order_index": x.order_index,
            "in_minimum_path": x.id in min_path,
        } for x in actions],
        "deadlines": dl_out, "requirements": req_out,
        "dependencies": [{"id": d.id, "from_action_id": d.from_action_id, "to_action_id": d.to_action_id, "reason": d.reason} for d in deps],
        "risks": [{"id": r.id, "description": r.description, "severity": r.severity, "stated_in_source": r.stated_in_source,
                   "confidence": r.confidence, "evidence": r.evidence, "evidence_status": r.evidence_status} for r in risks],
        "questions": [{"id": q.id, "question": q.question, "reason": q.reason} for q in qs],
        "minimum_path": min_path,
    }
    if include_raw:
        out["raw_text"] = a.raw_text
    return out
