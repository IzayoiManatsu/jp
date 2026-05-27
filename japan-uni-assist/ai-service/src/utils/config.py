from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://jua:jua_secret@localhost:5432/jua_db"
    redis_url: str = "redis://localhost:6379"
    default_model: str = "gpt-4o"
    log_level: str = "info"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()