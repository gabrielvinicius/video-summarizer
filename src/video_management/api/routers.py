# src/video_management/api/routers.py
import io
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, File, Query
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.dependencies import get_service, get_video_queries # Import the new query dependency
from src.shared.events.domain_events import TranscriptionRequested
from src.shared.events.event_bus import EventBus
from src.video_management.application.commands.upload_video_command import UploadVideoCommand
from src.video_management.application.video_service import VideoService
from src.video_management.application.queries.video_queries import VideoQueries # Import the query class
from .schemas import VideoResponse, VideoDetailResponse
from ..domain.video import Video, VideoStatus

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
    responses={404: {"description": "Not found"}},
)

ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED, summary="Create a new video by uploading a file")
async def create_video(
    file: UploadFile = File(...),
    storage_provider: Optional[str] = Query("local", description="The storage provider to use (e.g., 'local', 's3')."),
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_service("video_service")),
):
    """Uploads a video file to create a new video resource."""
    try:
        file_ext = file.filename.split('.')[-1] if file.filename else ''
        if f".{file_ext}" not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")

        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File too large. Max size is {MAX_FILE_SIZE // (1024 * 1024)}MB")

        command = UploadVideoCommand(user_id=str(current_user.id), file=await file.read(), filename=file.filename, storage_provider=storage_provider)
        video = await video_service.create_video(command)
        return jsonable_encoder(video)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}") from e


@router.get("/", response_model=List[VideoResponse], summary="List videos for the current user")
async def list_current_user_videos(
    skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), video_queries: VideoQueries = Depends(get_video_queries),
):
    """Lists all videos for the currently authenticated user."""
    videos = await video_queries.list_user_videos(user_id=str(current_user.id), skip=skip, limit=limit)
    return jsonable_encoder(videos)


@router.get("/{video_id}", response_model=VideoDetailResponse, summary="Get a specific video by its ID")
async def get_video_by_id(
    video_id: UUID, current_user: User = Depends(get_current_user), video_queries: VideoQueries = Depends(get_video_queries),
):
    """Retrieves detailed metadata for a specific video."""
    if current_user.role.value == "admin":
        video = await video_queries.get_video_by_id(video_id=str(video_id))
    else:
        video = await video_queries.get_video_by_user_by_id(video_id=str(video_id), user_id=str(current_user.id))
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return jsonable_encoder(video)


@router.post("/{video_id}/transcription", status_code=status.HTTP_202_ACCEPTED, summary="Request transcription for a video")
async def request_video_transcription(
    video_id: UUID,
    provider: Optional[str] = Query("whisper", description="The transcription provider to use (e.g., 'whisper', 'fastwhisper')."),
    video_queries: VideoQueries = Depends(get_video_queries),
    event_bus: EventBus = Depends(get_service("event_bus")),
):
    """Starts an asynchronous transcription process for a video."""
    video = await video_queries.get_video_by_id(str(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status == VideoStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="A transcription for this video is already in progress.")

    event = TranscriptionRequested(video_id=str(video.id), provider=provider)
    await event_bus.publish(event)
    return {"message": "Transcription requested successfully"}
