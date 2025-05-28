import io
import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from main import app  # sua app FastAPI principal
from src.shared.infrastructure.database import get_db
from src.video_management.domain.video import Video
from src.auth.utils.token import create_access_token  # sua função real

from tests.utils.db import override_get_db, setup_test_db


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    await setup_test_db()
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def auth_headers():
    # Simula um usuário com ID "user123"
    token = create_access_token(data={"sub": "user123"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_video(auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        video_bytes = b"fake_video_content"
        response = await client.post(
            "/videos/upload",
            headers=auth_headers,
            files={"file": ("test.mp4", io.BytesIO(video_bytes), "video/mp4")}
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "uploaded"


@pytest.mark.asyncio
async def test_list_user_videos(auth_headers):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/videos/me", headers=auth_headers)

    assert response.status_code == 200
    videos = response.json()
    assert isinstance(videos, list)
    assert len(videos) >= 1


@pytest.mark.asyncio
async def test_get_video_details(auth_headers):
    # Upload first to ensure there's a video
    async with AsyncClient(app=app, base_url="http://test") as client:
        upload = await client.post(
            "/videos/upload",
            headers=auth_headers,
            files={"file": ("test.mp4", io.BytesIO(b"video"), "video/mp4")}
        )
        video_id = upload.json()["id"]

        response = await client.get(f"/videos/{video_id}", headers=auth_headers)

    assert response.status_code == 200
    details = response.json()
    assert details["id"] == video_id
    assert details["status"] == "uploaded"
