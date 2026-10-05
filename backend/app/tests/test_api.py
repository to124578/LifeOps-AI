import json

from icalendar import Calendar

from .conftest import H, analyze, sample_text


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_1_empty_input_400(client):
    assert client.post("/api/analyze/text", json={"text": "   "}, headers=H).status_code == 400
    assert client.post("/api/analyze", data={"text": ""}, headers=H).status_code == 400


def test_2_unsupported_file_415(client):
    r = client.post("/api/analyze", files={"file": ("virus.exe", b"MZ....", "application/octet-stream")}, headers=H)
    assert r.status_code == 415
    r = client.post("/api/analyze", files={"file": ("fake.pdf", b"not a pdf", "application/pdf")}, headers=H)
    assert r.status_code == 415  # content does not match extension


def test_3_valid_text_creates_analysis(client):
    aid = analyze(client)
    a = client.get(f"/api/analysis/{aid}").json()
    assert a["status"] == "done", a.get("error")
    assert a["title"] and len(a["pipeline"]) == 5
    assert all(p["status"] in ("done", "degraded") for p in a["pipeline"])


def test_4_actions_stored(client):
    aid = analyze(client)
    tasks = client.get(f"/api/analysis/{aid}/tasks").json()
    assert len(tasks) >= 1 and tasks[0]["id"]


def test_5_deadline_preserved(client):
    aid = analyze(client, "fee")
    a = client.get(f"/api/analysis/{aid}").json()
    pay = next(d for d in a["deadlines"] if d["label"] == "Tuition fee payment")
    assert pay["kind"] == "hard" and pay["due_at"] and len(pay["due_at"]) == 10
    assert pay["evidence_status"] == "verified"


def test_6_task_completion_persists(client):
    aid = analyze(client)
    t = client.get(f"/api/analysis/{aid}/tasks").json()[0]
    assert client.post(f"/api/tasks/{t['id']}/complete", json={"completed": True}).status_code == 200
    again = client.get(f"/api/analysis/{aid}/tasks").json()
    assert next(x for x in again if x["id"] == t["id"])["status"] == "done"
    client.post(f"/api/tasks/{t['id']}/complete", json={"completed": False})
    assert next(x for x in client.get(f"/api/analysis/{aid}/tasks").json() if x["id"] == t["id"])["status"] == "todo"


def test_7_calendar_is_valid_ics(client):
    aid = analyze(client, "fee")
    r = client.get(f"/api/analysis/{aid}/calendar.ics")
    assert r.status_code == 200 and "text/calendar" in r.headers["content-type"]
    cal = Calendar.from_ical(r.content)
    events = [c for c in cal.walk() if c.name == "VEVENT"]
    assert len(events) == 4
    assert all(e.get("SUMMARY") and e.get("DTSTART") for e in events)


def test_8_export_json_and_markdown(client):
    aid = analyze(client, "licence")
    pack = client.get(f"/api/analysis/{aid}/export/json").json()
    assert pack["schema_id"] == "lifeops.actionpack/1.0"
    assert pack["tasks"] and pack["deadlines"] and pack["disclaimer"]
    json.dumps(pack)
    md = client.get(f"/api/analysis/{aid}/export/markdown").text
    assert md.startswith("# ") and "## Checklist" in md


def test_9_delete_session_removes_data(client):
    h = {"X-Session-Id": "to-delete"}
    aid = analyze(client, "offer", h)
    assert client.get(f"/api/analysis/{aid}").status_code == 200
    r = client.delete("/api/session/to-delete")
    assert r.status_code == 200 and r.json()["deleted_analyses"] == 1
    assert client.get(f"/api/analysis/{aid}").status_code == 404
    assert client.get("/api/analyses", headers=h).json() == []


def test_10_missing_api_key_clear_error(client, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post("/api/analyze/text", json={"text": "Pay the bill by Friday"}, headers=H)
    assert r.status_code == 503
    body = r.json()
    assert body["error"] == "ai_not_configured" and "GEMINI_API_KEY" in body["message"]
    assert "Traceback" not in r.text


def test_whatif_refuses_to_invent_consequence(client):
    aid = analyze(client, "offer")
    r = client.post(f"/api/analysis/{aid}/whatif", json={"preset": "miss"}).json()
    assert r["status"] == "unknown"
    assert "does not say" in r["answer"]


def test_whatif_states_consequence_when_source_has_it(client):
    aid = analyze(client, "fee")
    r = client.post(f"/api/analysis/{aid}/whatif", json={"preset": "miss"}).json()
    assert r["status"] == "answered" and "500" in r["answer"] and r["sources"]


def test_whatif_other_presets(client):
    aid = analyze(client, "licence")
    for p in ("before", "fastest", "delegate", "missing"):
        r = client.post(f"/api/analysis/{aid}/whatif", json={"preset": p})
        assert r.status_code == 200 and r.json()["answer"]


def test_deadline_shield_lists_prerequisites(client):
    aid = analyze(client, "offer")
    a = client.get(f"/api/analysis/{aid}").json()
    d1 = next(d for d in a["deadlines"] if d["key"] == "d1")
    assert d1["assumed_anchor"] and d1["due_at"]  # relative 24h resolved from analysis time, flagged
    titles = {p["title"] for p in d1["prerequisites"]}
    assert any("NOC" in t for t in titles) and len(d1["suggested_prerequisites"]) == 1


def test_samples_produce_different_plans(client):
    titles = set()
    for sid in ("offer", "fee", "licence"):
        a = client.get(f"/api/analysis/{analyze(client, sid)}").json()
        titles.add(a["title"])
    assert len(titles) == 3


def test_no_false_conflict_between_different_milestones(client):
    a = client.get(f"/api/analysis/{analyze(client, 'fee')}").json()
    assert not any("Conflicting" in n for n in a["verification_notes"])
