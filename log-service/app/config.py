from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    REDIS_URL: str = "redis://redis:6379/0"
    LOG_INTERNAL_TOKEN: str
    PORT: int = 8002

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "../../.env"), extra="ignore")


settings = Settings()
