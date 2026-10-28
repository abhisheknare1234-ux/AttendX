import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "AttendX AI — Smart Attendance & Anti-Proxy System"
    APP_VERSION: str = "1.0.0"
    INSTITUTION_NAME: str = "ZEAL College of Engineering & Research, Pune"

    # Security & JWT
    SECRET_KEY: str = "attendx_dev_secret_key_change_in_production_min_32_bytes_long!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Database
    DATABASE_URL: str = "sqlite:///./attendx.db"

    # Dynamic Attendance Verification Controls
    QR_REFRESH_INTERVAL_SECONDS: int = 30
    CHECKIN_WINDOW_MINUTES: int = 5
    PIN_DIGITS: int = 6
    PIN_MAX_ATTEMPTS: int = 5

    # Geofence Reference Anchor (ZEAL College of Engineering & Research, Narhe, Pune)
    CAMPUS_DEFAULT_LATITUDE: float = 18.4485
    CAMPUS_DEFAULT_LONGITUDE: float = 73.8245
    CAMPUS_DEFAULT_RADIUS_METERS: float = 100.0
    MAX_ALLOWED_LOCATION_ACCURACY_METERS: float = 80.0

    # Face Verification & Liveness Thresholds
    FACE_VERIFIER_PROVIDER: str = "internal"  # "internal", "external_provider", "simulated_eval"
    FACE_SIMILARITY_THRESHOLD: float = 0.75
    LIVENESS_PROVIDER: str = "passive_challenge"
    LIVENESS_REQUIRED: bool = False

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Initial Admin Bootstrap (can be provided via environment)
    INITIAL_ADMIN_EMAIL: str = "admin@zeal.attendx.ai"
    INITIAL_ADMIN_PASSWORD: str = "ZealAdmin@2026Secure!"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    def validate_production_readiness(self) -> None:
        """Enforce strict production checks to prevent insecure deployment."""
        if self.ENVIRONMENT.lower() == "production":
            if "change_in_production" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("CRITICAL SECURITY ERROR: Production deployment requires a secure, high-entropy SECRET_KEY (min 32 chars).")
            if "sqlite" in self.DATABASE_URL.lower():
                raise ValueError("CRITICAL DATABASE ERROR: Production deployment requires PostgreSQL, not local SQLite.")


settings = Settings()
