from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    TMDB_BASE_URL: str
    TMDB_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PORT: int = 8000
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    LOG_SERVICE_URL: str = "http://log-service:8002"
    LOG_INTERNAL_TOKEN: str = ""
    GRAFANA_INTERNAL_URL: str = "http://grafana:3000"
    PROMETHEUS_INTERNAL_URL: str = "http://prometheus:9090"
    PROMETHEUS_PROXY_PASSWORD: str = ""

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "../../.env"), extra="ignore")


settings = Settings()
