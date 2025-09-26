# src/video_management/api/dependencies.py
from functools import lru_cache
from src.video_management.config.settings import VideoSettings

@lru_cache()
def get_video_settings() -> VideoSettings:
    return VideoSettings()
