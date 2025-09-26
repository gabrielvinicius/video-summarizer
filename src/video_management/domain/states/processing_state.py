# src/video_management/domain/states/processing_state.py
from __future__ import annotations
from typing import TYPE_CHECKING

from .video_state import VideoState
from src.video_management.domain.video import VideoStatus

if TYPE_CHECKING:
    from .completed_state import CompletedState
    from .failed_state import FailedState


class ProcessingState(VideoState):
    """Represents the state of a video that is being processed."""

    def complete(self):
        """Transitions the video to the Completed state."""
        from .completed_state import CompletedState
        self._video.state = CompletedState(self._video)

    def fail(self, reason: str):
        """Transitions the video to the Failed state."""
        from .failed_state import FailedState
        self._video.state = FailedState(self._video, reason)

    @property
    def status(self) -> VideoStatus:
        return VideoStatus.PROCESSING
