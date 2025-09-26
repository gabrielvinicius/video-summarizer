# src/shared/events/domain_events.py
from dataclasses import dataclass, asdict
from abc import ABC
from typing import Optional


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for domain events."""
    def to_dict(self) -> dict:
        """Converts the event to a dictionary for serialization."""
        return asdict(self)


# --- Video Management Events ---

@dataclass(frozen=True)
class VideoUploaded(DomainEvent):
    """Event triggered when a video has been successfully uploaded."""
    video_id: str
    user_id: str


# --- Transcription Events ---

@dataclass(frozen=True)
class TranscriptionRequested(DomainEvent):
    """Event triggered when a transcription is explicitly requested for a video."""
    video_id: str
    provider: str

@dataclass(frozen=True)
class TranscriptionStarted(DomainEvent):
    video_id: str

@dataclass(frozen=True)
class TranscriptionCompleted(DomainEvent):
    video_id: str
    transcription_id: str

@dataclass(frozen=True)
class TranscriptionFailed(DomainEvent):
    video_id: str
    error: str


# --- Summarization Events ---

@dataclass(frozen=True)
class SummarizationRequested(DomainEvent):
    """Event triggered when a user requests a new summary."""
    transcription_id: str
    provider: str


@dataclass(frozen=True)
class SummarizationProgress(DomainEvent):
    """Event to report the progress of a summarization task."""
    transcription_id: str
    progress: int
    stage: str
    estimated_total_seconds: Optional[float] = None
