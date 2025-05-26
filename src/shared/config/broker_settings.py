# src/shared/config/settings.py
from pydantic_settings import BaseSettings


class BrokerSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        extra = "ignore"
