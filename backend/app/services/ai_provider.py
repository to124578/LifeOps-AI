# talks to the AI provider; everything goes through generate_json() so output is always validated
import base64
import json
import re
import time
from datetime import date
from typing import Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from ..core.config import Settings, get_settings
from ..core.errors import AIFailure, AINotConfigured
from . import samples as sample_lib

T = TypeVar("T", bound=BaseModel)


def _strip_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    # last resort: grab the outermost {...}
    if not t.startswith("{"):
        s, e = t.find("{"), t.rfind("}")
        if s != -1 and e > s:
            t = t[s : e + 1]
    return t


class AIProvider:
    name = "base"
    supports_vision = False

    def _raw_json(self, system: str, user: str) -> str:
        raise NotImplementedError

    def ocr(self, data: bytes, mime: str) -> str:
        raise AIFailure("This AI provider cannot read images or scanned PDFs.", 422, "vision_unsupported")

    def generate_json(self, system: str, user: str, schema: Type[T], task: str = "") -> T:
        raw = self._raw_json(system, user)
        try:
            return schema.model_validate_json(_strip_fences(raw))
        except (ValidationError, ValueError) as first_err:
            repair = (
                "Your previous reply was not valid JSON for the required schema.\n"
                f"Error: {str(first_err)[:600]}\n\nPrevious reply:\n{raw[:6000]}\n\n"
                "Return ONLY corrected JSON that matches the schema. No prose, no markdown fences."
            )
            raw2 = self._raw_json(system, user + "\n\n" + repair)
            try:
                return schema.model_validate_json(_strip_fences(raw2))
            except (ValidationError, ValueError):
                raise AIFailure("The AI returned malformed output twice. Please try again.", 502, "ai_malformed_output")


def _http_post(url: str, headers: dict, payload: dict, timeout: float) -> dict:
    waits = [3, 6, 12]  # when the provider is busy, wait this long and try again
    for attempt in range(len(waits) + 1):
        try:
            r = httpx.post(url, headers=headers, json=payload, timeout=timeout)
        except httpx.TimeoutException:
            raise AIFailure("The AI provider timed out. Please try again.", 504, "ai_timeout")
        except httpx.HTTPError:
            raise AIFailure("Could not reach the AI provider. Check your connection.", 502, "ai_unreachable")

        if r.status_code in (429, 500, 502, 503, 504) and attempt < len(waits):
            time.sleep(waits[attempt])
            continue

        if r.status_code in (401, 403):
            raise AIFailure("The AI provider rejected the API key. Check your key in backend/.env.", 503, "ai_bad_key")
        if r.status_code == 429:
            raise AIFailure("AI provider rate limit reached. Wait a minute and retry.", 429, "ai_rate_limited")
        if r.status_code == 503:
            raise AIFailure("Gemini is overloaded right now. Please try again in a minute.", 503, "ai_busy")
        if r.status_code >= 400:
            raise AIFailure(f"AI provider error (HTTP {r.status_code}).", 502, "ai_error")
        return r.json()
    raise AIFailure("AI provider is busy. Please retry shortly.", 503, "ai_busy")


class GeminiProvider(AIProvider):
    name = "gemini"
    supports_vision = True

    def __init__(self, s: Settings):
        self.s = s
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{s.gemini_model}:generateContent"
        self.headers = {"x-goog-api-key": s.gemini_api_key, "Content-Type": "application/json"}

    def _call(self, payload: dict) -> str:
        data = _http_post(self.url, self.headers, payload, self.s.ai_timeout_s)
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        except (KeyError, IndexError, TypeError):
            raise AIFailure("The AI returned an empty response (possibly blocked). Try rephrasing or another document.", 502, "ai_empty")

    def _raw_json(self, system, user):
        return self._call({
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1},
        })

    def ocr(self, data: bytes, mime: str) -> str:
        return self._call({
            "contents": [{"role": "user", "parts": [
                {"text": "Transcribe ALL text in this document/image exactly as written, preserving line breaks. Output only the transcription. If there is no readable text, output exactly: NO_TEXT"},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}},
            ]}],
            "generationConfig": {"temperature": 0},
        }).strip()


class OpenAICompatProvider(AIProvider):
    name = "openai"
    supports_vision = True

    def __init__(self, s: Settings):
        self.s = s
        self.url = f"{s.openai_base_url}/chat/completions"
        self.headers = {"Authorization": f"Bearer {s.openai_api_key}", "Content-Type": "application/json"}

    def _call(self, messages, json_mode=False) -> str:
        payload = {"model": self.s.openai_model, "messages": messages, "temperature": 0.1}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = _http_post(self.url, self.headers, payload, self.s.ai_timeout_s)
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            raise AIFailure("The AI returned an empty response.", 502, "ai_empty")

    def _raw_json(self, system, user):
        return self._call([{"role": "system", "content": system}, {"role": "user", "content": user}], json_mode=True)

    def ocr(self, data: bytes, mime: str) -> str:
        if not mime.startswith("image/"):
            raise AIFailure("This provider can read images but not scanned PDFs. Upload a screenshot instead.", 422, "vision_unsupported")
        url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
        return self._call([{"role": "user", "content": [
            {"type": "text", "text": "Transcribe ALL text in this image exactly as written, preserving line breaks. Output only the transcription. If none, output exactly: NO_TEXT"},
            {"type": "image_url", "image_url": {"url": url}},
        ]}]).strip()


class MockProvider(AIProvider):
    # canned answers for the 3 sample docs, only used when AI_PROVIDER=mock

    name = "mock"

    def __init__(self):
        self._today = date.today()

    def generate_json(self, system: str, user: str, schema: Type[T], task: str = "") -> T:
        m = re.search(r"TODAY:\s*(\d{4}-\d{2}-\d{2})", user)
        today = date.fromisoformat(m.group(1)) if m else date.today()
        if task == "whatif":
            raise AIFailure("Demo mode (AI_PROVIDER=mock) supports only the preset what-if questions. Set a real AI key for free-form questions.", 422, "mock_limit")
        s = sample_lib.find_by_text(user)
        if s is None:
            raise AIFailure("Demo mode (AI_PROVIDER=mock) only understands the 3 built-in samples. Set GEMINI_API_KEY to analyze your own documents.", 422, "mock_limit")
        data = s["u"] if task == "understanding" else s["p"]
        return schema.model_validate(sample_lib.render(data, today))

    def ocr(self, data, mime):
        raise AIFailure("Demo mode (AI_PROVIDER=mock) cannot read images or PDFs. Set GEMINI_API_KEY.", 422, "mock_limit")


def get_provider(settings: Optional[Settings] = None) -> AIProvider:
    s = settings or get_settings()
    if s.ai_provider == "mock":
        return MockProvider()
    if s.ai_provider in ("gemini", "openai"):
        if not s.api_key:
            raise AINotConfigured(s.ai_provider)
        return GeminiProvider(s) if s.ai_provider == "gemini" else OpenAICompatProvider(s)
    raise AIFailure(f"Unknown AI_PROVIDER '{s.ai_provider}'. Use gemini, openai or mock.", 503, "ai_not_configured")