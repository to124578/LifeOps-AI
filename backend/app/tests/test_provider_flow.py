# runs the real Gemini code path against a fake http layer
import json

from app.services import ai_provider

from .conftest import H

DOC = "Hi, the electricity bill of Rs. 1,840 must be paid by 20 October 2026. Pay online using your consumer number 55521."

UNDERSTANDING = {
    "title": "Electricity bill", "document_type": "utility bill", "summary": "Pay Rs. 1,840 by 20 Oct 2026.",
    "actions": [{"id": "a1", "title": "Pay the electricity bill", "priority": "high", "due_at": "2026-10-20", "confidence": "high",
                 "evidence": "the electricity bill of Rs. 1,840 must be paid by 20 October 2026"}],
    "deadlines": [{"id": "d1", "label": "Bill payment", "due_at": "2026-10-20", "kind": "hard", "action_ids": ["a1"], "confidence": "high",
                   "evidence": "must be paid by 20 October 2026"}],
    "requirements": [{"item": "Consumer number 55521", "required": True, "action_ids": ["a1"], "confidence": "high", "evidence": "consumer number 55521"}],
    "risks": [], "questions": [{"question": "What is the late fee?", "reason": "Not stated"}], "confidence": "high",
}
PLAN = {"ordered_action_ids": ["a1"], "dependencies": [], "minimum_path": ["a1"], "suggested_prerequisites": [], "notes": []}


def _gemini(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def test_real_provider_path_with_retry_on_malformed_json(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    calls = {"n": 0}

    def fake_post(url, headers, payload, timeout):
        calls["n"] += 1
        assert headers["x-goog-api-key"] == "fake-key"
        prompt = payload["contents"][0]["parts"][0]["text"]
        if "Extract the structured action data" in prompt and calls["n"] == 1:
            return _gemini("```json\n{ this is not valid json")  # forces the repair retry
        if "Extract the structured action data" in prompt:
            return _gemini("```json\n" + json.dumps(UNDERSTANDING) + "\n```")  # fenced JSON is tolerated
        return _gemini(json.dumps(PLAN))

    monkeypatch.setattr(ai_provider, "_http_post", fake_post)
    r = client.post("/api/analyze/text", json={"text": DOC, "client_now": "2026-10-04T09:00:00"}, headers=H)
    assert r.status_code == 202
    a = client.get(f"/api/analysis/{r.json()['id']}").json()
    assert a["status"] == "done", a["error"]
    assert a["title"] == "Electricity bill" and a["provider"].startswith("gemini:")
    assert a["actions"][0]["evidence_status"] == "verified"
    assert calls["n"] == 3  # malformed -> repair -> planning


def test_malformed_twice_fails_gracefully(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(ai_provider, "_http_post", lambda *a, **k: _gemini("nope"))
    r = client.post("/api/analyze/text", json={"text": DOC}, headers=H)
    a = client.get(f"/api/analysis/{r.json()['id']}").json()
    assert a["status"] == "failed" and "malformed" in a["error"] and "Traceback" not in a["error"]


def test_planning_failure_degrades_but_still_completes(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    def fake_post(url, headers, payload, timeout):
        prompt = payload["contents"][0]["parts"][0]["text"]
        return _gemini(json.dumps(UNDERSTANDING)) if "Extract the structured action data" in prompt else _gemini("garbage")

    monkeypatch.setattr(ai_provider, "_http_post", fake_post)
    r = client.post("/api/analyze/text", json={"text": DOC, "client_now": "2026-10-04T09:00:00"}, headers=H)
    a = client.get(f"/api/analysis/{r.json()['id']}").json()
    assert a["status"] == "done"
    assert next(p for p in a["pipeline"] if p["name"] == "planning")["status"] == "degraded"
    assert any("fallback" in n.lower() for n in a["verification_notes"])


def test_free_text_whatif_requires_grounding(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    def fake_post(url, headers, payload, timeout):
        prompt = payload["contents"][0]["parts"][0]["text"]
        if "QUESTION:" in prompt:  # model "hallucinates" a consequence with a made-up quote
            return _gemini(json.dumps({"answer": "Your power will be cut after 3 days.", "answerable": True, "quotes": ["power will be cut after 3 days"]}))
        return _gemini(json.dumps(UNDERSTANDING if "Extract the structured action data" in prompt else PLAN))

    monkeypatch.setattr(ai_provider, "_http_post", fake_post)
    r = client.post("/api/analyze/text", json={"text": DOC, "client_now": "2026-10-04T09:00:00"}, headers=H)
    aid = r.json()["id"]
    w = client.post(f"/api/analysis/{aid}/whatif", json={"question": "What if I pay late?"}).json()
    assert w["status"] == "unknown" and "cut" not in w["answer"]
