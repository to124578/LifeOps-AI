# stage 3: second AI call for ordering/dependencies, then cleanup in code
import json
from typing import Dict, List

from ...schemas.extraction import DependencyIn, Plan, Understanding

SYSTEM = """You are the Planning Agent of LifeOps AI. Given extracted actions, deadlines and requirements, produce an execution plan.

RULES
- Use only the action ids and deadline ids provided. Do not add new actions.
- ordered_action_ids: ALL action ids in the order a sensible person should do them (prerequisites first, earliest deadlines first).
- dependencies: {"from_action_id","to_action_id","reason"} meaning from MUST be finished before to. Only add a dependency when it is real (e.g. a document is needed to complete the next step). The graph must have no cycles.
- minimum_path: the smallest set of action ids that satisfies the REQUIRED obligations, in order. Exclude optional/conditional steps.
- suggested_prerequisites: practical things the person should do first that the source does not explicitly say (e.g. "contact X early"), each tied to a deadline_id. These are your suggestions, not source facts - keep them few (max 3) and useful.
- notes: up to 3 short planning remarks (bottlenecks, tight timing).
- Return ONLY one JSON object: {"ordered_action_ids":[...],"dependencies":[...],"minimum_path":[...],"suggested_prerequisites":[{"deadline_id":str,"description":str,"reason":str}],"notes":[str]}"""


def build_user(u: Understanding, raw_text: str, today: str) -> str:
    brief = {
        "actions": [{"id": a.id, "title": a.title, "owner": a.owner, "due_at": a.due_at, "priority": a.priority} for a in u.actions],
        "deadlines": [{"id": d.id, "label": d.label, "due_at": d.due_at, "date_text": d.date_text, "kind": d.kind, "action_ids": d.action_ids} for d in u.deadlines],
        "requirements": [{"item": r.item, "required": r.required, "action_ids": r.action_ids} for r in u.requirements],
    }
    return f"TODAY: {today}\n\nEXTRACTED:\n{json.dumps(brief, ensure_ascii=False)}\n\nSOURCE (for reference):\n<<<SOURCE\n{raw_text}\nSOURCE>>>"


def _fallback(u: Understanding) -> Plan:
    pri = {"high": 0, "medium": 1, "low": 2}
    ordered = sorted(u.actions, key=lambda a: (a.due_at or "9999", pri.get(a.priority, 1)))
    ids = [a.id for a in ordered]
    return Plan(ordered_action_ids=ids, minimum_path=ids, notes=["Planning agent unavailable; actions ordered by due date and priority."])


def _acyclic(deps: List[DependencyIn]) -> List[DependencyIn]:
    # drop any edge that would close a cycle
    kept: List[DependencyIn] = []
    adj: Dict[str, set] = {}

    def reaches(src: str, dst: str) -> bool:
        stack, seen = [src], set()
        while stack:
            n = stack.pop()
            if n == dst:
                return True
            if n in seen:
                continue
            seen.add(n)
            stack.extend(adj.get(n, ()))
        return False

    for d in deps:
        if d.from_action_id == d.to_action_id or reaches(d.to_action_id, d.from_action_id):
            continue
        adj.setdefault(d.from_action_id, set()).add(d.to_action_id)
        kept.append(d)
    return kept


def clean(plan: Plan, u: Understanding) -> Plan:
    ids = [a.id for a in u.actions]
    valid = set(ids)
    dids = {d.id for d in u.deadlines}
    ordered = [i for i in plan.ordered_action_ids if i in valid]
    ordered += [i for i in ids if i not in ordered]
    seen, deps = set(), []
    for d in plan.dependencies:
        k = (d.from_action_id, d.to_action_id)
        if d.from_action_id in valid and d.to_action_id in valid and k not in seen:
            seen.add(k)
            deps.append(d)
    plan.ordered_action_ids = ordered
    plan.dependencies = _acyclic(deps)
    plan.minimum_path = [i for i in plan.minimum_path if i in valid] or ordered
    plan.suggested_prerequisites = [s for s in plan.suggested_prerequisites if s.deadline_id is None or s.deadline_id in dids][:3]
    return plan


def run(provider, u: Understanding, raw_text: str, today: str):
    if not u.actions:
        return Plan(), False
    try:
        plan = provider.generate_json(SYSTEM, build_user(u, raw_text, today), Plan, task="planning")
        return clean(plan, u), False
    except Exception:
        return clean(_fallback(u), u), True
