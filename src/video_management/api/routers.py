from fastapi import APIRouter, UploadFile, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.auth.api.dependencies import get_current_user
from src.auth.domain.user import User
from src.video_management.application.video_service import VideoService
from .schemas import VideoUploadRequest, VideoResponse, VideoDetailResponse
from typing import List
from src.video_management.api.dependencies import get_video_service
from src.shared.infrastructure.database import get_db

from src.video_management.domain.video import Video

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload", response_model=VideoResponse)
async def upload_video(
        file: UploadFile,
        current_user: dict = Depends(get_current_user),
        video_service: VideoService = Depends(get_video_service),
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
async def get_video_details(video_id: str, video_service: VideoService = Depends(get_video_service)):
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
async def download_video(video_id: str, video_service: VideoService = Depends(get_video_service)):
    video = video_service.get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    file_content = await video_service.storage_service.download(video.file_path)
    return FileResponse(
        path=video.file_path,
        filename=video.file_path.split("/")[-1],
        content=file_content
    )

@router.get("/", response_model=List[VideoResponse])
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    videos = db.query(Video).offset(skip).limit(limit).all()
    return videos

@router.get("/me", response_model=List[VideoResponse])
async def list_user_videos(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Video).filter(Video.user_id == user.id).all()

from fastapi.responses import StreamingResponse

@router.get("/{video_id}/stream")
async def stream_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    def iterfile():
        with open(video.file_path, mode="rb") as file:
            yield from file

    return StreamingResponse(iterfile(), media_type="video/mp4")