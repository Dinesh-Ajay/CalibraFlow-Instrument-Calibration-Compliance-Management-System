from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "CalibraFlow — Instrument Calibration & Compliance Management System"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/calibraflow?charset=utf8mb4"
    TEST_DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/calibraflow_test?charset=utf8mb4"

    SECRET_KEY: str = "calibraflow-super-secure-production-ready-jwt-key-2026-industrial-compliance"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    GEMINI_API_KEY: Optional[str] = None

    # SMTP Configuration (supports standard names and provider aliases)
    SMTP_HOST: Optional[str] = None
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SENDER_EMAIL: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SENDER_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def _clean_str(self, val: Optional[str]) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            s = s[1:-1].strip()
        return s if s else None

    @property
    def resolved_smtp_host(self) -> Optional[str]:
        return self._clean_str(self.SMTP_HOST) or self._clean_str(self.SMTP_SERVER)

    @property
    def resolved_smtp_user(self) -> Optional[str]:
        return self._clean_str(self.SMTP_USER) or self._clean_str(self.SENDER_EMAIL)

    @property
    def resolved_smtp_password(self) -> Optional[str]:
        return self._clean_str(self.SMTP_PASSWORD) or self._clean_str(self.SENDER_PASSWORD)

    @property
    def resolved_smtp_from_email(self) -> str:
        explicit = self._clean_str(self.SMTP_FROM_EMAIL)
        if explicit and explicit != "noreply@calibraflow.internal":
            return explicit
        user_email = self.resolved_smtp_user
        if user_email and "@" in user_email:
            return user_email
        return explicit or "noreply@calibraflow.internal"

    @property
    def is_smtp_configured(self) -> bool:
        return bool(self.resolved_smtp_host and self.resolved_smtp_user and self.resolved_smtp_password)

    model_config = SettingsConfigDict(
        env_file=(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
