import io
import os
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
from src.transcription.tasks.tasks import process_transcription_task
from ..domain.video import Video, VideoStatus

router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    responses={404: {"description": "Not found"}},
)

# Tipos de arquivo permitidos
ALLOWED_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB


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
    """
    Upload a video file

    - **file**: Video file to upload (MP4, MOV, AVI, MKV, WEBM)
    - Returns: Uploaded video metadata
    """
    try:
        # Validação do tipo de arquivo
        file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        if file_ext not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(ALLOWED_EXTENSIONS)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {allowed}"
            )

        # Verificar tamanho do arquivo
        if file.size > MAX_FILE_SIZE:
            max_size_mb = MAX_FILE_SIZE // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {max_size_mb}MB"
            )

        # Processar upload
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
    responses={403: {"description": "Forbidden"}}
)
async def list_videos(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    List videos for the current user

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
    try:
        if current_user.role.value == "admin":
            # Admin can access any video
            video = await video_service.get_video_by_id(video_id=str(video_id))
            return jsonable_encoder(video)

        video = await video_service.get_video_by_user_by_id(
            video_id=str(video_id),
            user_id=str(current_user.id),
        )
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
    try:
        video: Video

        video = await video_service.get_video_by_user_by_id(
            video_id=str(video_id),
            user_id=str(current_user.id),
        )

        if current_user.role.value == "admin":
            # Admin can access any video
            video = await video_service.get_video_by_id(video_id=str(video_id))

        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        # Baixar o conteúdo
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
    responses={
        202: {"description": "Transcription started"},
        404: {"description": "Video not found"},
        403: {"description": "Access denied"},
        409: {"description": "Transcription already in progress"}
    }
)
async def start_transcription(
        video_id: UUID,
        current_user: User = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
):
    """
    Start asynchronous transcription for a video

    - **video_id**: UUID of the video to transcribe
    - Returns: Confirmation message
    """
    try:
        # Verificar permissões e estado do vídeo
        video = await video_service.get_video_by_user_by_id(
            video_id=str(video_id),
            user_id=str(current_user.id),
            # is_admin=(current_user.role.value == "admin")
        )

        if current_user.role.value == "admin":
            # Admin can access any video
            video = await video_service.get_video_by_id(video_id=str(video_id))

        # Verificar se a transcrição já está em andamento
        if video.status == VideoStatus.PROCESSING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transcription is already in progress"
            )

        # Publish event
        await video_service.event_bus.publish("video_uploaded", {
            "video_id": video.id,
            "file_path": video.file_path,
            "user_id": video.user_id
        })
        # Disparar tarefa de transcrição
        # process_transcription_task.delay(str(video_id))

        return {"message": "Transcription started successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start transcription: {str(e)}"
        ) from e
