from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from fastapi.responses import FileResponse
from src.auth.api.dependencies import get_current_user
from src.video_management.application.video_service import VideoService
from schemas import VideoUploadRequest, VideoResponse, VideoDetailResponse
from typing import List

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
        file: UploadFile,
        current_user: dict = Depends(get_current_user),
        video_service: VideoService = Depends(),
):
    try:
        video_data = await file.read()
        video = await video_service.upload_video(current_user["id"], video_data, file.filename)
        return VideoResponse(
            id=video.id,
            status=video.status.value,
            created_at=video.created_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no upload: {str(e)}"
        )


@router.get("/{video_id}", response_model=VideoDetailResponse)
async def get_video_details(video_id: str, video_service: VideoService = Depends()):
    video = video_service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    return VideoDetailResponse(
        id=video.id,
        status=video.status.value,
        created_at=video.created_at,
        transcription=video.transcription_id,
        summary=video.summary_id
    )


@router.get("/{video_id}/download")
async def download_video(video_id: str, video_service: VideoService = Depends()):
    video = video_service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    file_content = await video_service.storage_service.download(video.file_path)
    return FileResponse(
        path=video.file_path,
        filename=video.file_path.split("/")[-1],
        content=file_content
    )