# src/video_management/api/routers.py

import io
from typing import List, Sequence
from uuid import UUID

from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.video_management.api.dependencies import get_video_service
from src.video_management.application.video_service import VideoService
from .schemas import VideoResponse, VideoDetailResponse
from ..domain.video import Video

router = APIRouter(
    prefix="/videos",
    tags=["videos"],
)


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
):
    try:
        video_data = await file.read()
        video: Video = await video_service.upload_video(current_user.id, video_data, file.filename)
        return jsonable_encoder(VideoResponse(
            id=video.id,
            status=video.status.value,
            created_at=video.created_at
        ))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no upload: {str(e)}"
        )


@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    video_service: VideoService = Depends(get_video_service),
):
    if user.role.value == "admin":
        videos: Sequence[Video] = await video_service.list_all_videos(skip, limit)
    else:
        videos: Sequence[Video] = await video_service.list_user_videos(user.id)
    return jsonable_encoder(videos)


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video_details(
    video_id: UUID,
    video_service: VideoService = Depends(get_video_service)
):
    video: Video = await video_service.get_video_by_id(str(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    return jsonable_encoder(VideoDetailResponse(
        id=video.id,
        status=video.status.value,
        created_at=video.created_at,
        transcription=video.transcription_id,
        summary=video.summary_id
    ))


@router.get("/{video_id}/download")
async def download_video(
    video_id: UUID,
    video_service: VideoService = Depends(get_video_service)
):
    video: Video = await video_service.get_video_by_id(str(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    content = await video_service.storage_service.download(video.file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage")

    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{video.file_path.split("/")[-1]}"'
        }
    )
