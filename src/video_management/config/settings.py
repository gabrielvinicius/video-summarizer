# src/video_management/config/settings.py
from pydantic_settings import BaseSettings
from typing import Set

class VideoSettings(BaseSettings):
    allowed_extensions: Set[str] = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    max_file_size_mb: int = 200

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        extra = "ignore"
        env_prefix = "VIDEO_"
