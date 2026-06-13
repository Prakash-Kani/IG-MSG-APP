from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "IGMessenger"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "igmessenger"

    JWT_SECRET: str = "change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    STORAGE_BACKEND: str = "local"  # local | gdrive
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 50

    GDRIVE_FOLDER_ID: str = ""

    ENABLE_INAPP_NOTIFICATIONS: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
