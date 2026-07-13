from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ----------------------------
    # Application
    # ----------------------------
    APP_NAME: str = "AI API Gateway"
    APP_VERSION: str = "0.1.0"

    # ----------------------------
    # PostgreSQL
    # ----------------------------
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # ----------------------------
    # Redis
    # ----------------------------
    REDIS_HOST: str
    REDIS_PORT: int

    # ----------------------------
    # Computed Database URL
    # ----------------------------
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}"
            f"@localhost:5432/"
            f"{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()