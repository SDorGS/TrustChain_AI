from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustChain AI"
    VERSION: str = "1.0.0"
    APP_ENV: str = "development"

    DATABASE_URL: str = "sqlite:///./trustchain.db"

    SQUAD_SECRET_KEY: Optional[str] = None
    SQUAD_WEBHOOK_SECRET: Optional[str] = None
    SQUAD_BASE_URL: str = "https://sandbox-api-d.squadco.com"

    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024

    ALLOWED_CONTENT_TYPES: list[str] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
        ]
    )

    # =====================================================
    # TRUST SCORING CONFIG
    # =====================================================

    MARKET_AVG: int = 5000
    PRICE_THRESHOLD: float = 0.6

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()