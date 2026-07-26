from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application settings loaded from the .env file.
    Pydantic validates types automatically — if DATABASE_URL is missing
    or SECRET_KEY is empty, the app fails at startup with a clear error.
    """

    # Database
    database_url: str

    # Security
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # External APIs
    google_books_api_key: str = ""

    # OAuth — Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8009/api/v1/auth/google/callback"
    frontend_url: str = "http://localhost:5173"
    session_secret_key: str = "change-me-in-production"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    environment: str = "development"
    cors_origins: str = "http://localhost:5173"

    # Stage 2
    groq_api_key: str = ""
    openai_api_key: str = ""
    hf_token: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Split comma-separated CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    model_config = SettingsConfigDict(
        env_file=".env",        # look for .env in the current working directory
        env_file_encoding="utf-8",
        case_sensitive=False,   # DATABASE_URL and database_url both work
    )


# Single instance used throughout the app — import this everywhere
settings = Settings()
