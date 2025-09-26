# src/video_management/api/routers.py
import io
import os
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, File, Query
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.dependencies import get_service, get_video_queries
from src.video_management.application.commands.upload_video_command import UploadVideoCommand
from src.video_management.application.video_service import VideoService
from src.video_management.application.queries.video_queries import VideoQueries
from .schemas import VideoResponse, VideoDetailResponse
from .dependencies import get_video_settings
from ..config.settings import VideoSettings

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED, summary="Create a new video by uploading a file")
async def create_video(
    file: UploadFile = File(...),
    storage_provider: Optional[str] = Query("local", description="The storage provider to use (e.g., 'local', 's3')."),
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_service("video_service")),
    settings: VideoSettings = Depends(get_video_settings),
):
    """Uploads a video file to create a new video resource."""
    try:
        _, file_ext = os.path.splitext(file.filename or "")
        if file_ext.lower() not in settings.allowed_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file format. Allowed formats: {', '.join(settings.allowed_extensions)}")

        if file.size > settings.max_file_size_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File too large. Max size is {settings.max_file_size_mb}MB")

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
        video = await video_queries.get_by_id(video_id=str(video_id))
    else:
        video = await video_queries.get_video_by_user_by_id(video_id=str(video_id), user_id=str(current_user.id))
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return jsonable_encoder(video)


@router.post("/{video_id}/transcription", status_code=status.HTTP_202_ACCEPTED, summary="Request transcription for a video")
async def request_video_transcription(
    video_id: UUID,
    provider: Optional[str] = Query("whisper", description="The transcription provider to use (e.g., 'whisper', 'fastwhisper')."),
    video_service: VideoService = Depends(get_service("video_service")),
    # No need to inject video_queries or event_bus here anymore
):
    """Starts an asynchronous transcription process for a video."""
    try:
        await video_service.request_transcription(video_id=str(video_id), provider=provider)
        return {"message": "Transcription requested successfully"}
    except ValueError as e:
        # Handle specific business logic errors from the service layer
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start transcription: {str(e)}") from e
