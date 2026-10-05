class AppError(Exception):
    # safe to show to the user

    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


class AINotConfigured(AppError):
    def __init__(self, provider: str):
        env = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider, "AI_PROVIDER")
        super().__init__(
            503,
            "ai_not_configured",
            f"AI provider '{provider}' is not configured. Set {env} in backend/.env "
            f"(see .env.example) and restart the server, or set AI_PROVIDER=mock for the built-in samples only.",
        )


class AIFailure(AppError):
    def __init__(self, message: str, status: int = 502, code: str = "ai_error"):
        super().__init__(status, code, message)
