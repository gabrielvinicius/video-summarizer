# src/video_management/domain/states/completed_state.py
from __future__ import annotations
from typing import TYPE_CHECKING

from .video_state import VideoState
from src.video_management.domain.video import VideoStatus


class CompletedState(VideoState):
    """Represents the state of a video that has been successfully processed."""

    # No transitions are allowed from the completed state.
    # The default implementation in the base class will raise an error.

    @property
    def status(self) -> VideoStatus:
        return VideoStatus.COMPLETED
