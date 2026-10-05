# what-if answers. presets are answered from the stored plan; free text goes to the AI and its quotes get checked
import json
from typing import Dict, List

from ..schemas.extraction import WhatIfAI
from .verify import VERIFIED, PARTIAL, SourceIndex

PRESETS = {
    "miss": "What happens if I miss this?",
    "before": "What do I need before I start?",
    "fastest": "What is the fastest path?",
    "delegate": "What can I delegate?",
    "missing": "What information is missing?",
}

UNKNOWN_TAIL = "I won't guess - confirm this with the sender or the issuing office."


def _ok(item) -> bool:
    return item.get("evidence_status") in (VERIFIED, PARTIAL)


def answer_preset(kind: str, data: Dict) -> Dict:
    actions = {a["id"]: a for a in data["actions"]}
    open_actions = [a for a in data["actions"] if a["status"] != "done"]
    if kind == "miss":
        stated = [r for r in data["risks"] if r["stated_in_source"] and _ok(r)]
        inferred = [r for r in data["risks"] if not r["stated_in_source"]]
        if stated:
            lines = [f"- {r['description']}" for r in stated]
            return {"status": "answered", "method": "deterministic",
                    "answer": "The source states these consequences:\n" + "\n".join(lines) +
                              ("\n\nNot stated in the source (inferences, unverified):\n" + "\n".join(f"- {r['description']}" for r in inferred) if inferred else ""),
                    "sources": [{"quote": r["evidence"], "verified": r["evidence_status"] == VERIFIED} for r in stated], "verify_with": None}
        return {"status": "unknown", "method": "deterministic",
                "answer": "The document does not say what happens if you miss this deadline. " + UNKNOWN_TAIL +
                          ("\n\nPossible concerns the system noticed (NOT from the source):\n" + "\n".join(f"- {r['description']}" for r in inferred) if inferred else ""),
                "sources": [], "verify_with": "the sender / issuing office"}
    if kind == "before":
        reqs = [r for r in data["requirements"] if r["required"] and r["status"] != "have"]
        first = open_actions[0] if open_actions else None
        lines = [f"- {r['item']}" for r in reqs] or ["- The source lists no separate prerequisites."]
        ans = "Required items and documents:\n" + "\n".join(lines)
        if first:
            ans += f"\n\nA good first step: {first['title']}."
        return {"status": "answered", "method": "deterministic", "answer": ans,
                "sources": [{"quote": r["evidence"], "verified": r["evidence_status"] == VERIFIED} for r in reqs if r.get("evidence")], "verify_with": None}
    if kind == "fastest":
        path = [actions[i] for i in data["minimum_path"] if i in actions and actions[i]["status"] != "done"]
        if not path:
            return {"status": "answered", "method": "deterministic", "answer": "Nothing left on the minimum path - everything required is done.", "sources": [], "verify_with": None}
        mins = sum(a["effort_minutes"] or 0 for a in path)
        known = all(a["effort_minutes"] for a in path)
        eff = f"\n\nEstimated active effort: about {mins} min{'' if known else ' (some steps have no estimate)'}. Effort estimates are AI guesses, not from the source."
        return {"status": "answered", "method": "deterministic",
                "answer": "Minimum path, in order:\n" + "\n".join(f"{n}. {a['title']}" for n, a in enumerate(path, 1)) + eff, "sources": [], "verify_with": None}
    if kind == "delegate":
        yes = [a for a in open_actions if a["can_delegate"] is True]
        no = [a for a in open_actions if a["can_delegate"] is False]
        others = [a for a in open_actions if a["owner"] and not a["owner"].lower().startswith(("you", "me", "recipient", "student", "proprietor"))]
        parts = []
        if yes:
            parts.append("The source allows someone else to do:\n" + "\n".join(f"- {a['title']}" for a in yes))
        if no:
            parts.append("The source requires you personally for:\n" + "\n".join(f"- {a['title']}" for a in no))
        if others:
            parts.append("Owned by someone else already:\n" + "\n".join(f"- {a['title']} ({a['owner']})" for a in others))
        unknown = [a for a in open_actions if a["can_delegate"] is None and a not in others]
        if unknown:
            parts.append("Delegation is not mentioned for:\n" + "\n".join(f"- {a['title']}" for a in unknown))
        return {"status": "partial" if unknown else "answered", "method": "deterministic",
                "answer": "\n\n".join(parts) + ("\n\n" + UNKNOWN_TAIL if unknown else ""),
                "sources": [{"quote": a["evidence"], "verified": a["evidence_status"] == VERIFIED} for a in yes + no if a.get("evidence")],
                "verify_with": "the sender" if unknown else None}
    if kind == "missing":
        qs = [f"- {q['question']} ({q['reason']})" if q["reason"] else f"- {q['question']}" for q in data["questions"]]
        nv = [f"- {d['label']}: no exact date in the source" for d in data["deadlines"] if not d["due_at"]]
        nv += [f"- '{a['title']}': claim not confirmed by the source text" for a in data["actions"] if a["needs_verification"]]
        body = qs + nv
        return {"status": "answered" if body else "answered", "method": "deterministic",
                "answer": ("Open questions and unverified items:\n" + "\n".join(body)) if body else "Nothing obviously missing - all extracted items are supported by the source text.",
                "sources": [], "verify_with": None}
    raise KeyError(kind)


SYSTEM = """You answer a user's what-if question about ONE document, using ONLY the SOURCE text and the EXTRACTED PLAN below.
RULES
- If the source/plan does not establish the answer, set answerable=false and say plainly that it is not stated. NEVER invent consequences, fees, dates, rules or names.
- Keep the answer short and practical (max 120 words).
- quotes: up to 3 VERBATIM quotes from the SOURCE that support the answer. Empty if answerable=false.
- verify_with: who/what to check with when something is unknown, else null.
- Return ONLY JSON: {"answer": str, "answerable": bool, "quotes": [str], "verify_with": str|null}"""


def answer_free(provider, data: Dict, question: str, today: str) -> Dict:
    brief = {
        "actions": [{"title": a["title"], "owner": a["owner"], "due_at": a["due_at"], "status": a["status"]} for a in data["actions"]],
        "deadlines": [{"label": d["label"], "due_at": d["due_at"], "kind": d["kind"]} for d in data["deadlines"]],
        "requirements": [r["item"] for r in data["requirements"]],
        "stated_risks": [r["description"] for r in data["risks"] if r["stated_in_source"]],
    }
    user = f"TODAY: {today}\n\nEXTRACTED PLAN:\n{json.dumps(brief, ensure_ascii=False)}\n\nSOURCE:\n<<<SOURCE\n{data['raw_text']}\nSOURCE>>>\n\nQUESTION: {question}"
    r = provider.generate_json(SYSTEM, user, WhatIfAI, task="whatif")
    idx = SourceIndex(data["raw_text"])
    srcs = [{"quote": q, "verified": idx.status(q) == VERIFIED} for q in r.quotes[:3]]
    grounded = any(s["verified"] or idx.status(s["quote"]) == PARTIAL for s in srcs)
    if r.answerable and not grounded:
        return {"status": "unknown", "method": "ai",
                "answer": "I could not find support for an answer in the document text, so I won't state one. " + UNKNOWN_TAIL,
                "sources": [], "verify_with": r.verify_with or "the sender / issuing office"}
    return {"status": "answered" if r.answerable else "unknown", "method": "ai", "answer": r.answer, "sources": srcs,
            "verify_with": r.verify_with}
