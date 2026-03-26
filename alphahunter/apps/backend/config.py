import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str = "alphahunter"
    DB_PASSWORD: str = "alpha123"
    DB_NAME: str = "alphahunter_dev"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    ANTHROPIC_API_KEY: str = ""
    MINO_API_KEY: str = ""
    TINYFISH_RUN_SSE_URL: str = "https://mino.ai/v1/automation/run-sse"
    TINYFISH_DEFAULT_TIMEOUT_SECS: int = 20

    @property
    def DATABASE_URL(self) -> str:
        # Fallback to sqlite if host is localhost to aid local rapid dev without docker
        if self.DB_HOST == "localhost" and self.DB_NAME == "alphahunter_dev":
            return "sqlite:///./alphahunter_dev.db"
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        env_file = "../../../.env"
        # Optional: support .env in the backend folder as well for convenience
        # env_file = ".env" if running in backend

settings = Settings()
