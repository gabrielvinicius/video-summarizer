# src/notifications/config/settings.py
from pydantic_settings import BaseSettings


class SmtpSettings(BaseSettings):
    smtp_host: str = "smtp.mailtrap.io"
    smtp_port: int = 2525
    smtp_user: str = "user"
    smtp_password: str = "password"

    class Config:
        env_file = ".env"
        extra = "ignore"
