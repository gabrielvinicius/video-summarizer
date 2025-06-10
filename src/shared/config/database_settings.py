from pydantic_settings import BaseSettings
from functools import cached_property


class DatabaseSettings(BaseSettings):
    db_scheme: str = "postgresql"
    db_user: str
    db_password: str
    db_host: str
    db_port: int = 5432
    db_name: str

    class Config:
        env_file = ".env"
        extra = "ignore"

    @cached_property
    def database_url(self) -> str:
        return f"{self.db_scheme}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
