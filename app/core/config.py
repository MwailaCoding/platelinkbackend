# app/core/config.py
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PlateLink Africa"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # DATABASE
    # On Render, the injected DATABASE_URL uses the legacy postgres:// prefix.
    # RENDER_DATABASE_URL overrides DATABASE_URL and is auto-converted to postgresql+asyncpg://.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:2030@localhost:5432/platelink"
    RENDER_DATABASE_URL: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        """If RENDER_DATABASE_URL is set, convert and use it as DATABASE_URL."""
        if self.RENDER_DATABASE_URL:
            url = self.RENDER_DATABASE_URL
            # Render injects postgres:// — asyncpg requires postgresql+asyncpg://
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self.DATABASE_URL = url
        return self

    # REDIS
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS — comma-separated list of allowed origins, or "*" for all
    ALLOWED_ORIGINS: str = "*"

    # MPESA
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_CALLBACK_URL: Optional[str] = None
    MPESA_INITIATOR_NAME: str = "PlateLinkAdmin"
    MPESA_SECURITY_CREDENTIAL: str = "encrypted_credential"
    
    # CLOUDINARY
    CLOUDINARY_URL: Optional[str] = None
    
    # EMAIL
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = "PlateLink Africa"
    
    # SMS
    SMS_API_KEY: Optional[str] = None
    SMS_SENDER_ID: Optional[str] = "PLATELINK"

    # BREVO
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: Optional[str] = None
    BREVO_SENDER_NAME: Optional[str] = "PlateLink Africa"

    # PESAPAL
    PESAPAL_CONSUMER_KEY: Optional[str] = None
    PESAPAL_CONSUMER_SECRET: Optional[str] = None
    PESAPAL_ENVIRONMENT: Optional[str] = "sandbox"
    PESAPAL_API_URL: Optional[str] = None
    PESAPAL_CALLBACK_URL: Optional[str] = None
    PESAPAL_IPN_ID: Optional[str] = None

    # OPENAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000
    AI_EXTRACTION_TIMEOUT_SECONDS: int = 60
    AI_MAX_FILE_SIZE_MB: int = 20

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()

