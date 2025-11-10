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


settings = Settings()
