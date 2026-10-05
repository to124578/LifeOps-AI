# pulls text out of uploads (OCR for images is done in intake via the AI provider)
import io
from typing import Tuple

from pypdf import PdfReader

from ..core.errors import AppError

ALLOWED = {
    ".txt": ("text/plain", "txt"),
    ".md": ("text/plain", "txt"),
    ".pdf": ("application/pdf", "pdf"),
    ".png": ("image/png", "image"),
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".webp": ("image/webp", "image"),
}

MAGIC = {
    "pdf": [b"%PDF"],
    "image": [b"\x89PNG", b"\xff\xd8\xff", b"RIFF"],
}


def classify_upload(filename: str, data: bytes) -> Tuple[str, str]:
    name = (filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    if ext not in ALLOWED:
        raise AppError(415, "unsupported_file_type", "Unsupported file type. Upload a PDF, PNG/JPG/WEBP image, or .txt file.")
    mime, stype = ALLOWED[ext]
    if not data:
        raise AppError(400, "empty_input", "The uploaded file is empty.")
    if stype in MAGIC and not any(data.startswith(m) for m in MAGIC[stype]):
        raise AppError(415, "unsupported_file_type", "The file content does not match its extension.")
    return mime, stype


def pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise AppError(422, "pdf_encrypted", "This PDF is password-protected. Remove the password and try again.")
        parts = [(p.extract_text() or "") for p in reader.pages[:30]]
    except AppError:
        raise
    except Exception:
        raise AppError(422, "pdf_unreadable", "Could not read this PDF. It may be corrupted.")
    return "\n".join(parts).strip()


def txt_text(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return ""
