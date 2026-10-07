from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_PAGE_ID: str = ""
    META_PAGE_ACCESS_TOKEN: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = "meta_lead_poc_token_2026"
    META_API_VERSION: str = "v21.0"
    DATABASE_PATH: str = "leads.db"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
