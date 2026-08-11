from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # ── General ────────────────────────────────────────────────
    ENV: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "VeriIA Ecuador API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    PORT: int = 3008

    # ── CORS ───────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"

    # ── Uploads (solo en memoria/temporal, nada se persiste) ──
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png,.webp"

    # ── IA ─────────────────────────────────────────────────────
    AI_PROVIDER: str = "mock"  # mock | ollama | openai | google
    AI_ENABLED: bool = True
    AI_TIMEOUT_SECONDS: int = 60

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TEXT_MODEL: str = "llama3.1"
    OLLAMA_VISION_MODEL: str = "llava"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TEXT_MODEL: str = "gpt-4o-mini"
    OPENAI_VISION_MODEL: str = "gpt-4o-mini"

    GOOGLE_AI_API_KEY: str = ""
    GOOGLE_AI_BASE_URL: str = "https://generativelanguage.googleapis.com"
    GOOGLE_AI_TEXT_MODEL: str = "gemini-2.0-flash"
    GOOGLE_AI_VISION_MODEL: str = "gemini-2.0-flash"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_image_extensions_list(self) -> list[str]:
        return [
            e.strip().lower()
            for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")
            if e.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
