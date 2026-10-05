from datetime import date, datetime

from app.schemas.extraction import Plan, Understanding
from app.services import calendar as cal
from app.services import samples
from app.services.agents import planning, verification
from app.services.verify import NONE, PARTIAL, UNSUPPORTED, VERIFIED, SourceIndex


def test_all_sample_evidence_is_verbatim():
    """Canned outputs must quote the sample text exactly - keeps the demo 'verified'."""
    today = date(2026, 10, 4)
    for s in samples.SAMPLES:
        text = samples.render(s["text"], today)
        u = Understanding.model_validate(samples.render(s["u"], today))
        idx = SourceIndex(text)
        for coll in (u.actions, u.deadlines, u.requirements):
            for it in coll:
                if it.evidence:
                    assert idx.status(it.evidence) == VERIFIED, (s["id"], it.evidence)
        for r in u.risks:
            if r.stated_in_source:
                assert idx.status(r.evidence) == VERIFIED, (s["id"], r.evidence)


def test_evidence_status_levels():
    idx = SourceIndex("Please submit the form by 5 October 2026 at the front desk.")
    assert idx.status("submit the form by 5 October 2026") == VERIFIED
    assert idx.status("Please submit the form by 5th October, 2026 at front desk") in (VERIFIED, PARTIAL)
    assert idx.status("A penalty of 50% applies after the due date") == UNSUPPORTED
    assert idx.status(None) == NONE


def test_hallucinated_evidence_is_demoted():
    src = "Pay the fee by 10 Oct 2026."
    u = Understanding.model_validate({
        "title": "t", "actions": [{"id": "a1", "title": "Pay", "confidence": "high", "evidence": "Pay the fee by 10 Oct 2026."}],
        "deadlines": [{"id": "d1", "label": "Pay", "due_at": "2026-10-10", "kind": "hard", "action_ids": ["a1"], "confidence": "high", "evidence": "Payment must be made before midnight on the 10th"}],
        "risks": [{"description": "Account suspended", "stated_in_source": True, "confidence": "high", "evidence": "Your account will be suspended"}],
        "confidence": "high"})
    v = verification.run(u, Plan(ordered_action_ids=["a1"]), src, "2026-10-04T10:00")
    d = v["deadlines"][0]
    assert d["evidence_status"] == UNSUPPORTED and d["confidence"] == "low" and d["needs_verification"]
    assert v["risks"][0]["stated_in_source"] is False  # demoted to inference
    assert v["overall_confidence"] in ("low", "medium")


def test_planning_cleanup_drops_cycles_and_unknown_ids():
    u = Understanding.model_validate({"title": "t", "actions": [{"id": "a1", "title": "x"}, {"id": "a2", "title": "y"}]})
    p = Plan.model_validate({"ordered_action_ids": ["a2", "zzz"], "dependencies": [
        {"from_action_id": "a1", "to_action_id": "a2"}, {"from_action_id": "a2", "to_action_id": "a1"}, {"from_action_id": "a1", "to_action_id": "nope"}]})
    c = planning.clean(p, u)
    assert c.ordered_action_ids == ["a2", "a1"] and len(c.dependencies) == 1


def test_ics_structure_folding_and_escaping():
    ev = {"uid": "x@y", "summary": "Deadline: Pay, now; ok", "start": "2026-10-10", "all_day": True,
          "description": "Line one\nLine two " + "long " * 40}
    ics = cal.build_ics([ev], now=datetime(2026, 10, 4))
    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.endswith("END:VCALENDAR\r\n")
    assert all(len(l.encode()) <= 75 for l in ics.split("\r\n"))
    assert "DTSTART;VALUE=DATE:20261010" in ics and "\\," in ics and "\\;" in ics
    timed = cal.build_ics([{**ev, "start": "2026-10-10T09:30", "all_day": False}])
    assert "DTSTART:20261010T093000" in timed
