import io
import os
import asyncio
import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, File
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.shared.events.domain_events import VideoUploaded
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


@router.post(
    "/",  # Changed from /upload to be more RESTful
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new video by uploading a file",
    responses={
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"},
        500: {"description": "Upload failed"}
    }
)
async def create_video(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Uploads a video file to create a new video resource.

    - **file**: Video file to upload (MP4, MOV, AVI, MKV, WEBM)
    - Returns: Uploaded video metadata
    """
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {allowed}"
            )

        # Check file size
        if file.size > MAX_FILE_SIZE:
            max_size_mb = MAX_FILE_SIZE // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {max_size_mb}MB"
            )

        # Process upload (the service already publishes the event)
        video = await video_service.upload_video(
            user_id=str(current_user.id),
            file=await file.read(),
            filename=file.filename
        )

        return jsonable_encoder(video)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        ) from e


@router.get(
    "/",
    response_model=List[VideoResponse],
    summary="List videos for the current user",
    responses={403: {"description": "Forbidden"}}
)
async def list_current_user_videos(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Lists all videos for the currently authenticated user.

    - **skip**: Pagination offset
    - **limit**: Max items per page (default 100)
    - Returns: List of video metadata
    """
    try:
        videos = await video_service.list_user_videos(
            user_id=str(current_user.id),
            skip=skip,
            limit=limit
        )
        return jsonable_encoder(videos)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch videos"
        ) from e


@router.get(
    "/{video_id}",
    response_model=VideoDetailResponse,
    summary="Get a specific video by its ID",
    responses={
        404: {"description": "Video not found"},
        403: {"description": "Access denied"}
    }
)
async def get_video_by_id(
        video_id: UUID,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Retrieves detailed metadata for a specific video.

    - **video_id**: UUID of the video
    - Returns: Detailed video metadata
    """
    try:
        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))
        else:
            video = await video_service.get_video_by_user_by_id(
                video_id=str(video_id),
                user_id=str(current_user.id),
            )
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        return jsonable_encoder(video)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get video details"
        ) from e


@router.get(
    "/{video_id}/download",
    summary="Download the video file",
    responses={
        404: {"description": "Video not found"},
        403: {"description": "Access denied"},
        410: {"description": "Video file unavailable"}
    }
)
async def download_video(
        video_id: UUID,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Downloads the raw video file.

    - **video_id**: UUID of the video
    - Returns: Video file stream
    """
    try:
        video: Video
        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))
        else:
            video = await video_service.get_video_by_user_by_id(
                video_id=str(video_id),
                user_id=str(current_user.id),
            )

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        content, filename = await video_service.storage_service.download(video.file_path)

        if content is None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Video file unavailable in storage"
            )

        return StreamingResponse(
            io.BytesIO(content),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content))
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        ) from e


@router.post(
    "/{video_id}/transcription",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request transcription for a video",
    responses={
        202: {"description": "Transcription started"},
        404: {"description": "Video not found"},
        403: {"description": "Access denied"},
        409: {"description": "Transcription already in progress"}
    }
)
async def request_video_transcription(
        video_id: UUID,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Starts an asynchronous transcription process for a video.

    - **video_id**: UUID of the video to transcribe
    - Returns: Confirmation message
    """
    try:
        video = await video_service.get_video_by_user_by_id(
            video_id=str(video_id),
            user_id=str(current_user.id),
        )

        if current_user.role.value == "admin":
            video = await video_service.get_video_by_id(video_id=str(video_id))

        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if video.status == VideoStatus.PROCESSING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transcription is already in progress"
            )

        event = VideoUploaded(video_id=str(video.id), user_id=str(video.user_id))
        await video_service.event_bus.publish(event)

        return {"message": "Transcription requested successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start transcription: {str(e)}"
        ) from e

@router.get("/events", summary="Get real-time video status events (SSE)")
async def video_events(
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Server-Sent Events (SSE) endpoint for real-time video status updates.
    """
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
