# stage 1: get the text, guess language and doc type (no AI call unless OCR is needed)
from dataclasses import dataclass, field
from typing import List, Optional

from ...core.errors import AppError
from ..extraction import pdf_text, txt_text


@dataclass
class UploadPayload:
    filename: str
    data: bytes
    mime: str
    source_type: str  # txt | pdf | image


@dataclass
class IntakeResult:
    raw_text: str
    source_type: str
    language: str
    doc_type_hint: str
    truncated: bool = False
    notes: List[str] = field(default_factory=list)


_SCRIPTS = [
    ("hi", 0x0900, 0x097F, "Hindi/Devanagari"),
    ("bn", 0x0980, 0x09FF, "Bengali"),
    ("ta", 0x0B80, 0x0BFF, "Tamil"),
    ("ar", 0x0600, 0x06FF, "Arabic"),
    ("zh", 0x4E00, 0x9FFF, "Chinese"),
    ("ja", 0x3040, 0x30FF, "Japanese"),
    ("ko", 0xAC00, 0xD7AF, "Korean"),
    ("ru", 0x0400, 0x04FF, "Cyrillic"),
]

_TYPES = {
    "job offer / employment": ["offer letter", "internship", "stipend", "joining", "salary", "hr@"],
    "fee / payment notice": ["tuition", "fee", "invoice", "payment", "due date", "challan", "bill"],
    "renewal / compliance notice": ["renewal", "licence", "license", "expires", "compliance", "permit"],
    "government / legal notice": ["notice", "hereby", "tribunal", "court", "tax", "authority"],
    "medical / insurance": ["appointment", "prescription", "insurance", "claim", "policy", "patient"],
}


def detect_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "unknown"
    for code, lo, hi, _ in _SCRIPTS:
        if sum(1 for c in letters if lo <= ord(c) <= hi) / len(letters) > 0.3:
            return code
    return "en"  # Latin script assumed English (heuristic)


def guess_type(text: str) -> str:
    low = text.lower()
    scores = {k: sum(low.count(w) for w in ws) for k, ws in _TYPES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def run(text: Optional[str], upload: Optional[UploadPayload], provider, max_chars: int) -> IntakeResult:
    notes: List[str] = []
    if upload is None:
        raw, stype = (text or "").strip(), "text"
    elif upload.source_type == "txt":
        raw, stype = txt_text(upload.data), "txt"
    elif upload.source_type == "pdf":
        raw, stype = pdf_text(upload.data), "pdf"
        if len(raw) < 20:  # scanned PDF -> vision OCR
            notes.append("PDF had no text layer; used vision OCR.")
            raw = provider.ocr(upload.data, "application/pdf")
    else:
        raw, stype = provider.ocr(upload.data, upload.mime), "image"
        notes.append("Text read from image via vision model; check it for OCR mistakes.")
    raw = (raw or "").strip()
    if raw == "NO_TEXT" or len(raw) < 10:
        raise AppError(422, "no_readable_text", "No readable text was found in that input.")
    truncated = len(raw) > max_chars
    if truncated:
        raw = raw[:max_chars]
        notes.append(f"Input was truncated to the first {max_chars:,} characters.")
    return IntakeResult(raw, stype, detect_language(raw), guess_type(raw), truncated, notes)
