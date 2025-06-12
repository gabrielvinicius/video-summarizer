import io
from typing import List
from uuid import UUID
from fastapi import APIRouter, UploadFile, Depends, HTTPException, status, File
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.video_management.api.dependencies import get_video_service
from src.video_management.application.video_service import VideoService
from .schemas import VideoResponse, VideoDetailResponse

router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/upload",
    response_model=VideoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid file format"},
        413: {"description": "File too large"},
        500: {"description": "Upload failed"}
    }
)
async def upload_video(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    try:
        # Validação do tipo de arquivo
        if not file.filename or not file.filename.lower().endswith(('.mp4', '.mov', '.avi')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only MP4, MOV and AVI files are allowed"
            )

        # Lê o conteúdo para verificar o tamanho
        video_data = await file.read()
        max_size = 100 * 1024 * 1024  # 100MB

        if len(video_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {max_size // (1024 * 1024)}MB"
            )

        # Passa os dados binários para o service
        video = await video_service.upload_video(
            user_id=str(current_user.id),
            file=video_data,
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
    responses={403: {"description": "Forbidden"}}
)
async def list_videos(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    List videos

    - **skip**: Pagination offset
    - **limit**: Max items per page (default 100)
    - Returns: List of video metadata
    """
    try:
        if current_user.role.value == "admin":
            videos = await video_service.list_all_videos(skip, limit)
        else:
            videos = await video_service.list_user_videos(str(current_user.id))

        return jsonable_encoder(videos)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch videos"
        ) from e

@router.get(
    "/{video_id}",
    response_model=VideoDetailResponse,
    responses={
        404: {"description": "Video not found"},
        403: {"description": "Access denied"}
    }
)
async def get_video_details(
        video_id: UUID,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Get video details

    - **video_id**: UUID of the video
    - Returns: Detailed video metadata
    """
    video = await video_service.get_video_by_id(str(video_id))
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Verify ownership (unless admin)
    if current_user.role.value != "admin" and str(video.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this video"
        )

    return jsonable_encoder(video)

@router.get(
    "/{video_id}/download",
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
    Download video file

    - **video_id**: UUID of the video
    - Returns: Video file stream
    """
    video = await video_service.get_video_by_id(str(video_id))
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # Verify ownership (unless admin)
    if current_user.role.value != "admin" and str(video.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this video"
        )

    try:
        content = await video_service.storage_service.download(video.file_path)
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Video file unavailable in storage"
            )

        return StreamingResponse(
            io.BytesIO(content),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="{video.file_path.split("/")[-1]}"',
                "Content-Length": str(len(content))
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        ) from e

@router.get(
    "/{video_id}/transcription"
)
async def transcription_video(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Trigger asynchronous transcription for a video.
    """
    from src.transcription.tasks.tasks import process_transcription_task
    process_transcription_task.delay(video_id)
    # service.process_transcription(str(video_id))
    return {"message": "Transcription started"}