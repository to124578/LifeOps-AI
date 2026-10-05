import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    ai_provider: str
    gemini_api_key: str
    gemini_model: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    max_input_chars: int
    max_upload_mb: int
    database_url: str
    cors_origins: list
    ai_timeout_s: float

    @property
    def api_key(self) -> str:
        if self.ai_provider == "gemini":
            return self.gemini_api_key
        if self.ai_provider == "openai":
            return self.openai_api_key
        return "mock"

    @property
    def model(self) -> str:
        if self.ai_provider == "gemini":
            return self.gemini_model
        if self.ai_provider == "openai":
            return self.openai_model
        return "mock"


def get_settings() -> Settings:
    # read env each call so tests can override it
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "gemini").strip().lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        max_input_chars=int(os.getenv("MAX_INPUT_CHARS", "20000")),
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "8")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./lifeops.db"),
        cors_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
        ai_timeout_s=float(os.getenv("AI_TIMEOUT_S", "60")),
    )
