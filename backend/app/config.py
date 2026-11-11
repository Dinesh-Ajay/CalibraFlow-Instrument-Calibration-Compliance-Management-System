from pydantic_settings import BaseSettings
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
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@calibraflow.internal"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
