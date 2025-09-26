# src/video_management/domain/states/uploaded_state.py
from __future__ import annotations
from typing import TYPE_CHECKING

from .video_state import VideoState
from src.video_management.domain.video import VideoStatus

if TYPE_CHECKING:
    from src.video_management.domain.video import Video
    from .processing_state import ProcessingState
    from .failed_state import FailedState


class UploadedState(VideoState):
    """Represents the state of a video that has been successfully uploaded."""

    def process(self):
        """Transitions the video to the Processing state."""
        from .processing_state import ProcessingState
        self._video.state = ProcessingState(self._video)

    def fail(self, reason: str):
        """Transitions the video to the Failed state."""
        from .failed_state import FailedState
        self._video.state = FailedState(self._video, reason)

    @property
    def status(self) -> VideoStatus:
        return VideoStatus.UPLOADED
