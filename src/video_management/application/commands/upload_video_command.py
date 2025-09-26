# src/video_management/application/commands/upload_video_command.py
from dataclasses import dataclass

@dataclass(frozen=True)
class UploadVideoCommand:
    user_id: str
    file: bytes
    filename: str
    storage_provider: str
