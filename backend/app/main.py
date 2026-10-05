import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.config import get_settings
from .core.db import init_db
from .core.errors import AppError


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LifeOps AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error(_: Request, e: AppError):
    return JSONResponse(status_code=e.status, content={"error": e.code, "message": e.message})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "invalid_request", "message": "The request was not valid. Check your input and try again."})


@app.exception_handler(Exception)
async def unhandled(_: Request, e: Exception):  # don't leak stack traces
    return JSONResponse(status_code=500, content={"error": "server_error", "message": "Unexpected server error. Please try again."})


app.include_router(router)

# serve the built frontend from the same service
"""DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": "not_found", "message": "Not found."})
        f = DIST / path
        return FileResponse(f if path and f.is_file() else DIST / "index.html")
"""
# serve the built frontend from the same service
DIST = Path(os.getenv("FRONTEND_DIST", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    # CRITICAL: This MUST be the last route defined in your file
    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        # Let FastAPI handle /api paths natively by letting them pass through 
        # or handle file routing safely for the frontend
        f = DIST / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(DIST / "index.html")