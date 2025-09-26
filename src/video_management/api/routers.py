import io
import os
import asyncio
import json
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, File, Query
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
# Import the correct event for this action
from src.shared.events.domain_events import TranscriptionRequested
from src.video_management.api.dependencies import get_video_service
from src.video_management.application.video_service import VideoService
from .schemas import VideoResponse, VideoDetailResponse
from ..domain.video import Video, VideoStatus

router = APIRouter(
    prefix="/videos",
    tags=["Videos"],
    responses={404: {"description": "Not found"}},
)

# Allowed file types
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


@router.post("/", response_model=VideoResponse, status_code=status.HTTP_201_CREATED, summary="Create a new video by uploading a file")
async def create_video(
        file: UploadFile = File(...),
        storage_provider: Optional[str] = Query("local", description="The storage provider to use (e.g., 'local', 's3')."),
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """Uploads a video file to create a new video resource."""
    try:
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")

        if file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File too large. Max size is {MAX_FILE_SIZE // (1024 * 1024)}MB")

        video = await video_service.upload_video(user_id=str(current_user.id), file=await file.read(), filename=file.filename, storage_provider=storage_provider)
        return jsonable_encoder(video)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}") from e


@router.get("/", response_model=List[VideoResponse], summary="List videos for the current user")
async def list_current_user_videos(
        skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), video_service: VideoService = Depends(get_video_service),
):
    """Lists all videos for the currently authenticated user."""
    try:
        videos = await video_service.list_user_videos(user_id=str(current_user.id), skip=skip, limit=limit)
        return jsonable_encoder(videos)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch videos") from e


@router.get("/{video_id}", response_model=VideoDetailResponse, summary="Get a specific video by its ID")
async def get_video_by_id(
        video_id: UUID, current_user: User = Depends(get_current_user), video_service: VideoService = Depends(get_video_service),
):
    """Retrieves detailed metadata for a specific video."""
    try:
        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))
        else:
            video = await video_service.get_video_by_user_by_id(video_id=str(video_id), user_id=str(current_user.id))
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return jsonable_encoder(video)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get video details") from e


@router.get("/{video_id}/download", summary="Download the video file")
async def download_video(
        video_id: UUID, current_user: User = Depends(get_current_user), video_service: VideoService = Depends(get_video_service),
):
    """Downloads the raw video file."""
    try:
        video: Video
        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))
        else:
            video = await video_service.get_video_by_user_by_id(video_id=str(video_id), user_id=str(current_user.id))

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        storage_service = video_service.storage_service_factory(video.storage_provider)
        content, filename = await storage_service.download(video.file_path)

        if content is None:
            raise HTTPException(status_code=410, detail="Video file unavailable in storage")

        return StreamingResponse(io.BytesIO(content), media_type="video/mp4", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Download failed: {str(e)}") from e


@router.post("/{video_id}/transcription", status_code=status.HTTP_202_ACCEPTED, summary="Request transcription for a video")
async def request_video_transcription(
        video_id: UUID,
        provider: Optional[str] = Query("whisper", description="The transcription provider to use (e.g., 'whisper', 'fastwhisper')."),
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """Starts an asynchronous transcription process for a video."""
    try:
        video = await video_service.get_video_by_user_by_id(video_id=str(video_id), user_id=str(current_user.id))

        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if video.status == VideoStatus.PROCESSING:
            raise HTTPException(status_code=409, detail="Transcription is already in progress")

        # Publish the correct, more specific event
        event = TranscriptionRequested(video_id=str(video.id), provider=provider)
        await video_service.event_bus.publish(event)

        return {"message": "Transcription requested successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start transcription: {str(e)}") from e

@router.get("/events", summary="Get real-time video status events (SSE)")
async def video_events(
    current_user: User = Depends(get_current_user), video_service: VideoService = Depends(get_video_service),
):
    """Server-Sent Events (SSE) endpoint for real-time video status updates."""
    async def event_generator():
        videos = await video_service.list_user_videos(user_id=str(current_user.id))
        for video in videos:
            yield f"data: {json.dumps({'type': 'INITIAL', 'video': video.model_dump()})}\n\n"

        while True:
            await asyncio.sleep(5)
            updated_videos = await video_service.list_user_videos(user_id=str(current_user.id))
            for video in updated_videos:
                yield f"data: {json.dumps({'type': 'UPDATE', 'video': video.model_dump()})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
