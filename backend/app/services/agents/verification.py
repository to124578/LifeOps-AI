# stage 4: plain code, no AI. checks every quote against the source
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from ...schemas.extraction import Plan, Understanding
from ..verify import NONE, PARTIAL, UNSUPPORTED, VERIFIED, SourceIndex, adjust_confidence

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?$")
_DOMAIN_WORDS = {
    "legal": ["court", "tribunal", "lawsuit", "legal", "attorney", "contract"],
    "medical": ["patient", "prescription", "diagnosis", "hospital", "medical", "clinic"],
    "financial": ["tax", "loan", "invoice", "fee", "payment", "premium", "emi"],
    "immigration": ["visa", "immigration", "passport", "residence permit"],
    "employment": ["offer letter", "employment", "salary", "stipend", "payroll"],
    "government": ["municipal", "government", "licence", "license", "department of"],
}


def parse_due(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip().replace("Z", "")
    if not _DATE_RE.match(s):
        return None
    try:
        datetime.fromisoformat(s)
    except ValueError:
        return None
    return s[:16]


def _to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s if "T" in s else s + "T23:59")


def parse_local(s: Optional[str]) -> datetime:
    try:
        return datetime.fromisoformat((s or "").replace("Z", "")[:19])
    except ValueError:
        return datetime.utcnow()


def run(u: Understanding, plan: Plan, raw_text: str, client_now: str, anchor: Optional[str] = None, planning_degraded: bool = False) -> Dict:
    idx = SourceIndex(raw_text)
    now = parse_local(client_now)
    anchor_dt = parse_local(anchor) if anchor else now
    notes: List[str] = list(u.verification_notes)
    stats = {VERIFIED: 0, PARTIAL: 0, UNSUPPORTED: 0, NONE: 0}
    action_ids = {a.id for a in u.actions}

    def annotate(item) -> Dict:
        st = idx.status(item.evidence)
        stats[st] += 1
        return {
            "evidence": item.evidence,
            "evidence_status": st,
            "confidence": adjust_confidence(item.confidence, st),
            "needs_verification": st in (UNSUPPORTED, NONE),
        }

    actions = []
    for a in u.actions:
        ann = annotate(a)
        due = parse_due(a.due_at)
        if a.due_at and not due:
            notes.append(f"Action '{a.title}' had an unreadable date '{a.due_at}'; date removed.")
            ann["needs_verification"] = True
        actions.append({**a.model_dump(), **ann, "due_at": due})

    deadlines = []
    for d in u.deadlines:
        ann = annotate(d)
        due = parse_due(d.due_at)
        assumed = False
        if d.due_at and not due:
            notes.append(f"Deadline '{d.label}' had an unreadable date '{d.due_at}'; date removed.")
        if not due and d.relative_hours:
            due = (anchor_dt + timedelta(hours=float(d.relative_hours))).strftime("%Y-%m-%dT%H:%M")
            assumed = True
            notes.append(f"'{d.label}' is relative ({d.date_text or d.relative_hours}); counted from {anchor_dt:%d %b %Y %H:%M}.")
        if not due:
            ann["needs_verification"] = True
            notes.append(f"Deadline '{d.label}' has no exact date in the source - needs verification.")
        elif not assumed and _to_dt(due) < now:
            notes.append(f"Deadline '{d.label}' ({due}) appears to be in the past.")
        links = [i for i in d.action_ids if i in action_ids]
        deadlines.append({**d.model_dump(), **ann, "due_at": due, "assumed_anchor": assumed, "action_ids": links})

    # contradictions: only flag deadlines that look like the same milestone
    by_action: Dict[str, List[Dict]] = {}
    for d in deadlines:
        for i in d["action_ids"]:
            by_action.setdefault(i, []).append(d)
    for i, ds in by_action.items():
        hard = [d for d in ds if d["kind"] == "hard" and d["due_at"]]
        for x in range(len(hard)):
            for y in range(x + 1, len(hard)):
                a1, a2 = hard[x], hard[y]
                same = SequenceMatcher(None, a1["label"].lower(), a2["label"].lower()).ratio() > 0.6
                if same and a1["due_at"][:10] != a2["due_at"][:10]:
                    notes.append(f"Conflicting dates for '{a1['label']}': {a1['due_at'][:10]} vs {a2['due_at'][:10]}.")
    for a in actions:
        hard = [d for d in by_action.get(a["id"], []) if d["kind"] == "hard" and d["due_at"]]
        if a["due_at"] and len(hard) == 1 and a["due_at"][:10] != hard[0]["due_at"][:10]:
            notes.append(f"Action '{a['title']}' date ({a['due_at'][:10]}) differs from its deadline '{hard[0]['label']}' ({hard[0]['due_at'][:10]}).")

    requirements = []
    for r in u.requirements:
        ann = annotate(r)
        links = [i for i in r.action_ids if i in action_ids]
        if not links:
            notes.append(f"Requirement '{r.item}' is not linked to any task - confirm how you obtain it.")
        requirements.append({**r.model_dump(), **ann, "action_ids": links})

    risks = []
    for r in u.risks:
        if r.evidence or r.stated_in_source:
            ann = annotate(r)
        else:  # model's own inference: no quote expected
            ann = {"evidence": None, "evidence_status": NONE, "confidence": "low", "needs_verification": True}
        stated = r.stated_in_source
        if stated and ann["evidence_status"] in (UNSUPPORTED, NONE):
            stated = False  # demote: claimed as stated but the quote is not in the source
            ann["confidence"] = "low"
            notes.append(f"Risk '{r.description[:60]}' was claimed as stated in the source but could not be confirmed - shown as an inference.")
        risks.append({**r.model_dump(), **ann, "stated_in_source": stated})

    # plan
    keys = {a["id"] for a in actions}
    deps = [d.model_dump() for d in plan.dependencies if d.from_action_id in keys and d.to_action_id in keys]
    order = {i: n for n, i in enumerate(plan.ordered_action_ids)}
    for a in actions:
        a["order_index"] = order.get(a["id"], len(order))
    actions.sort(key=lambda a: a["order_index"])
    if planning_degraded:
        notes.append("Planning agent was unavailable; fallback ordering used and no dependencies were inferred.")
    notes.extend(plan.notes)

    total = max(1, sum(stats.values()))
    bad = (stats[UNSUPPORTED] + stats[NONE]) / total
    base = u.confidence
    if bad >= 0.3:
        overall = "low"
    elif stats[UNSUPPORTED] or stats[PARTIAL] or any(a["needs_verification"] for a in deadlines):
        overall = "medium" if base == "high" else base
    else:
        overall = base
    if stats[UNSUPPORTED]:
        notes.append(f"{stats[UNSUPPORTED]} extracted item(s) quote text that is not in the source; they are marked Low / Needs verification.")

    domains = [d for d in u.sensitive_domains if d in _DOMAIN_WORDS]
    if not domains:
        low = raw_text.lower()
        domains = [k for k, ws in _DOMAIN_WORDS.items() if any(w in low for w in ws)][:3]

    seen, clean_notes = set(), []
    for n in notes:
        if n not in seen:
            seen.add(n)
            clean_notes.append(n)

    return {
        "actions": actions, "deadlines": deadlines, "requirements": requirements, "risks": risks,
        "questions": [q.model_dump() for q in u.questions], "dependencies": deps,
        "minimum_path": plan.minimum_path, "suggested_prerequisites": [s.model_dump() for s in plan.suggested_prerequisites],
        "notes": clean_notes, "overall_confidence": overall, "sensitive_domains": domains, "stats": stats,
    }
