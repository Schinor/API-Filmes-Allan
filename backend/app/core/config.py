from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    TMDB_BASE_URL: str
    TMDB_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "../../.env"), extra="ignore")

settings = Settings()