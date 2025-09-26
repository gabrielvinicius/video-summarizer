# src/video_management/domain/states/video_state.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.video_management.domain.video import Video


class VideoState(ABC):
    """The Abstract Base Class for all video states (State Pattern)."""

    def __init__(self, video: Video):
        self._video = video

    @abstractmethod
    def process(self):
        """Transitions the video to a processing state."""
        raise NotImplementedError("This action is not allowed in the current state.")

    @abstractmethod
    def complete(self):
        """Transitions the video to a completed state."""
        raise NotImplementedError("This action is not allowed in the current state.")

    @abstractmethod
    def fail(self, reason: str):
        """Transitions the video to a failed state."""
        raise NotImplementedError("This action is not allowed in the current state.")
