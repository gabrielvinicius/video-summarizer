# src/video_management/domain/states/failed_state.py
from __future__ import annotations
from typing import TYPE_CHECKING

from .video_state import VideoState
from src.video_management.domain.video import VideoStatus

if TYPE_CHECKING:
    from .processing_state import ProcessingState


class FailedState(VideoState):
    """Represents the state of a video that has failed processing."""

    def __init__(self, video, reason: str):
        super().__init__(video)
        self._video.error_message = reason

    def process(self):
        """Allows reprocessing a failed video."""
        from .processing_state import ProcessingState
        self._video.error_message = None # Clear the error on retry
        self._video.state = ProcessingState(self._video)

    @property
    def status(self) -> VideoStatus:
        return VideoStatus.FAILED
