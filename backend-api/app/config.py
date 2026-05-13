from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OPTI Support Escalation API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg2://opti_user:opti_password@localhost:5432/opti_alerting"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()