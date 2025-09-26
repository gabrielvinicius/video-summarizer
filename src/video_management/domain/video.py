# src/video_management/domain/video.py
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, ForeignKey, event
from sqlalchemy.dialects.postgresql import UUID

from src.shared.infrastructure.database import Base
# Import state classes
from .states.video_state import VideoState
from .states.uploaded_state import UploadedState
from .states.processing_state import ProcessingState
from .states.completed_state import CompletedState
from .states.failed_state import FailedState


class VideoStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(SqlEnum(VideoStatus), default=VideoStatus.UPLOADED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    storage_provider = Column(String, nullable=False)
    error_message = Column(String, nullable=True)  # Field for failure reason

    _state: VideoState = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set initial state upon creation
        self._state = UploadedState(self)

    @property
    def state(self) -> VideoState:
        return self._state

    @state.setter
    def state(self, new_state: VideoState):
        """When the state object changes, update the persisted status column."""
        self._state = new_state
        self.status = new_state.status

    # --- State Transition Methods ---
    def process(self):
        """Delegates the process action to the current state object."""
        self.state.process()

    def complete(self):
        """Delegates the complete action to the current state object."""
        self.state.complete()

    def fail(self, reason: str):
        """Delegates the fail action to the current state object."""
        self.state.fail(reason)


# --- SQLAlchemy Event Listener to Reconstitute State ---

STATE_MAP = {
    VideoStatus.UPLOADED: UploadedState,
    VideoStatus.PROCESSING: ProcessingState,
    VideoStatus.COMPLETED: CompletedState,
    VideoStatus.FAILED: FailedState,
}

@event.listens_for(Video, 'load')
def _reconstitute_state(video: Video, _):
    """
    When a Video object is loaded from the DB, this event listener
    re-creates the correct state object based on the 'status' column.
    """
    status = video.status
    if status in STATE_MAP:
        if status == VideoStatus.FAILED:
            video._state = FailedState(video, video.error_message or "Unknown error")
        else:
            video._state = STATE_MAP[status](video)
    else:
        # Default to a safe state if status is somehow invalid
        video._state = UploadedState(video)
