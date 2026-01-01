"""Application settings loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = (
        "mysql+aiomysql://rtmc:rtmc_pass@db:3306/rtmc"
    )

    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Security
    SECRET_KEY: str

    # CORS — list of allowed origins (Streamlit runs on 8501 by default)
    CORS_ORIGINS: list[str] = ["http://localhost:8501"]

    # ── Password reset ────────────────────────────────────────────────────────
    # Base URL of the Streamlit frontend — used to build the reset link.
    FRONTEND_BASE_URL: str = "http://localhost:8501"

    # How long a reset token remains valid (minutes).
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    # ── SMTP / email ──────────────────────────────────────────────────────────
    # Leave SMTP_HOST empty to disable email sending (useful in development).
    # When DEBUG=true and SMTP_HOST is empty the reset URL is logged instead.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    # Set SMTP_USE_TLS=true for implicit TLS (port 465).
    SMTP_USE_TLS: bool = False
    # Set SMTP_START_TLS=true to upgrade a plain connection via STARTTLS (port 587).
    SMTP_START_TLS: bool = True

    EMAIL_FROM: str = "noreply@rt-modelcard.local"


settings = Settings()
