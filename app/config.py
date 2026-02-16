"""
Step 1 — Configuration from environment variables.
Uses pydantic-settings: loads from env and optionally .env, validates types.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Required and optional settings. Missing required vars raise at startup."""

    # Databases (required)
    DATABASE_URL: str
    MONGODB_URL: str
    REDIS_URL: str

    # Auth (required)
    JWT_SECRET: str

    # Optional
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  
    APP_NAME: str = "EdgeChat Backend"
    # CORS: comma-separated origins, or "*" for all (Step 5)
    CORS_ORIGINS: str = "*"
    # Rate limit (Step 6): max requests per IP per window
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single instance — import and use: from app.config import settings
settings = Settings()
