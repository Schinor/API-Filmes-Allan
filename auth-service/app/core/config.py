from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    PORT: int = 8001

    # Mailtrap / SMTP
    MAILTRAP_HOST: str = "sandbox.smtp.mailtrap.io"
    MAILTRAP_PORT: int = 2525
    MAILTRAP_USERNAME: str = ""
    MAILTRAP_PASSWORD: str = ""
    MAILTRAP_FROM_EMAIL: str = "nao-responda@tomhanksfilmes.com"
    MAILTRAP_FROM_NAME: str = "Tom Hanks Filmes"

    # URL base pública do catálogo para geração do link no e-mail
    CATALOGO_URL: str = "http://localhost:8000"

    # Expiração do token de redefinição de senha em minutos (30 minutos)
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "../../.env"), extra="ignore")


settings = Settings()
