from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MAX_UPLOAD_MB: int = 50
    DATA_DIR: str = "./data"
    DATABASE_URL: str = "sqlite:///./data/app.db"

settings = Settings()
