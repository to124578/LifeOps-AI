import json
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.db import get_db
from ..core.errors import AIFailure, AppError
from ..models.db_models import ANALYSIS_CHILD_TABLES, Action, Analysis, Deadline
from ..services import calendar as cal
from ..services import export, samples, whatif
from ..services.agents.intake import UploadPayload
from ..services.ai_provider import get_provider
from ..services.extraction import classify_upload
from ..services.pipeline import run_pipeline
from ..services.serialize import serialize_analysis

router = APIRouter(prefix="/api")


class TextIn(BaseModel):
    text: str = ""
    client_now: Optional[str] = None
    received_at: Optional[str] = None
    title: Optional[str] = None


class CompleteIn(BaseModel):
    completed: bool = True


class WhatIfIn(BaseModel):
    question: str = ""
    preset: Optional[str] = None


def _sid(x_session_id: Optional[str]) -> str:
    return (x_session_id or "anonymous").strip()[:64]


def _get(db: Session, analysis_id: str) -> Analysis:
    a = db.get(Analysis, analysis_id)
    if not a:
        raise AppError(404, "not_found", "Analysis not found (it may have been deleted).")
    return a


def _start(db, bg, session_id, text, upload, source_name, client_now, received_at) -> dict:
    get_provider()  # fail fast with a clear 503 setup error if the key is missing
    a = Analysis(id=uuid.uuid4().hex, session_id=session_id, source_name=source_name,
                 source_type=upload.source_type if upload else "text",
                 client_now=(client_now or datetime.utcnow().isoformat())[:19], status="processing", stage="queued", title="Analyzing...")
    db.add(a)
    db.commit()
    bg.add_task(run_pipeline, a.id, text, upload, (received_at or None))
    return {"id": a.id, "status": "processing"}


@router.get("/health")
def health():
    s = get_settings()
    configured = s.ai_provider == "mock" or bool(s.api_key)
    return {"status": "ok", "ai_provider": s.ai_provider, "model": s.model, "ai_configured": configured, "demo_mode": s.ai_provider == "mock"}


@router.get("/samples")
def get_samples(today: Optional[str] = None):
    try:
        d = date.fromisoformat(today) if today else date.today()
    except ValueError:
        d = date.today()
    return samples.list_samples(d)


@router.post("/analyze/text", status_code=202)
def analyze_text(body: TextIn, bg: BackgroundTasks, db: Session = Depends(get_db), x_session_id: Optional[str] = Header(None)):
    s = get_settings()
    text = (body.text or "").strip()
    if not text:
        raise AppError(400, "empty_input", "Please paste some text or upload a file.")
    if len(text) > s.max_input_chars * 5:
        raise AppError(413, "input_too_large", f"That text is too long (limit {s.max_input_chars:,} characters).")
    return _start(db, bg, _sid(x_session_id), text, None, "pasted text", body.client_now, body.received_at)


@router.post("/analyze", status_code=202)
async def analyze(bg: BackgroundTasks, file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None),
                  client_now: Optional[str] = Form(None), received_at: Optional[str] = Form(None),
                  db: Session = Depends(get_db), x_session_id: Optional[str] = Header(None)):
    s = get_settings()
    if file is None or not file.filename:
        t = (text or "").strip()
        if not t:
            raise AppError(400, "empty_input", "Please paste some text or upload a file.")
        if len(t) > s.max_input_chars * 5:
            raise AppError(413, "input_too_large", f"That text is too long (limit {s.max_input_chars:,} characters).")
        return _start(db, bg, _sid(x_session_id), t, None, "pasted text", client_now, received_at)
    data = await file.read(s.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > s.max_upload_mb * 1024 * 1024:
        raise AppError(413, "file_too_large", f"File is too large (limit {s.max_upload_mb} MB).")
    mime, stype = classify_upload(file.filename, data)
    return _start(db, bg, _sid(x_session_id), None, UploadPayload(file.filename, data, mime, stype), file.filename, client_now, received_at)


@router.get("/analyses")
def list_analyses(db: Session = Depends(get_db), x_session_id: Optional[str] = Header(None)):
    rows = db.query(Analysis).filter_by(session_id=_sid(x_session_id)).order_by(Analysis.created_at.desc()).limit(10).all()
    return [{"id": r.id, "title": r.title, "status": r.status, "document_type": r.document_type,
             "created_at": r.created_at.isoformat() + "Z", "overall_confidence": r.overall_confidence} for r in rows]


@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    return serialize_analysis(db, _get(db, analysis_id))


@router.get("/analysis/{analysis_id}/tasks")
def get_tasks(analysis_id: str, db: Session = Depends(get_db)):
    return serialize_analysis(db, _get(db, analysis_id), include_raw=False)["actions"]


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: str, body: CompleteIn = CompleteIn(), db: Session = Depends(get_db)):
    t = db.get(Action, task_id)
    if not t:
        raise AppError(404, "not_found", "Task not found.")
    t.status = "done" if body.completed else "todo"
    t.completed_at = datetime.utcnow() if body.completed else None
    db.commit()
    return serialize_analysis(db, _get(db, t.analysis_id))


@router.post("/deadlines/{deadline_id}/complete")
def complete_deadline(deadline_id: str, body: CompleteIn = CompleteIn(), db: Session = Depends(get_db)):
    d = db.get(Deadline, deadline_id)
    if not d:
        raise AppError(404, "not_found", "Deadline not found.")
    d.status = "done" if body.completed else "open"
    db.commit()
    return serialize_analysis(db, _get(db, d.analysis_id))


@router.get("/analysis/{analysis_id}/calendar.ics")
def calendar_ics(analysis_id: str, deadline_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    data = serialize_analysis(db, _get(db, analysis_id), include_raw=False)
    events = export.events_from(data, deadline_id)
    if not events:
        raise AppError(404, "no_events", "No deadline with an exact date to export. Deadlines without a date need verification first.")
    return Response(cal.build_ics(events), media_type="text/calendar; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="lifeops-deadlines.ics"'})


@router.get("/analysis/{analysis_id}/export/json")
def export_json(analysis_id: str, db: Session = Depends(get_db)):
    data = serialize_analysis(db, _get(db, analysis_id), include_raw=False)
    pack = export.build_pack(data).model_dump()
    return JSONResponse(pack, headers={"Content-Disposition": 'attachment; filename="lifeops-action-pack.json"'})


@router.get("/analysis/{analysis_id}/export/markdown")
def export_md(analysis_id: str, db: Session = Depends(get_db)):
    data = serialize_analysis(db, _get(db, analysis_id), include_raw=False)
    return PlainTextResponse(export.to_markdown(data), media_type="text/markdown; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="lifeops-action-pack.md"'})


@router.get("/actionpack/schema")
def pack_schema():
    return export.ActionPack.model_json_schema()


@router.post("/analysis/{analysis_id}/whatif")
def what_if(analysis_id: str, body: WhatIfIn, db: Session = Depends(get_db)):
    a = _get(db, analysis_id)
    if a.status != "done":
        raise AppError(409, "not_ready", "The analysis is not finished yet.")
    data = serialize_analysis(db, a)
    if body.preset:
        if body.preset not in whatif.PRESETS:
            raise AppError(400, "bad_preset", "Unknown preset question.")
        return {"question": whatif.PRESETS[body.preset], **whatif.answer_preset(body.preset, data)}
    q = (body.question or "").strip()
    if not q:
        raise AppError(400, "empty_input", "Type a question first.")
    if len(q) > 500:
        raise AppError(400, "question_too_long", "Keep the question under 500 characters.")
    provider = get_provider()
    return {"question": q, **whatif.answer_free(provider, data, q, (a.client_now or "")[:10] or date.today().isoformat())}


@router.delete("/session/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    ids = [r.id for r in db.query(Analysis.id).filter_by(session_id=session_id).all()]
    for model in ANALYSIS_CHILD_TABLES:
        if ids:
            db.query(model).filter(model.analysis_id.in_(ids)).delete(synchronize_session=False)
    db.query(Analysis).filter_by(session_id=session_id).delete(synchronize_session=False)
    db.commit()
    return {"deleted_analyses": len(ids)}
