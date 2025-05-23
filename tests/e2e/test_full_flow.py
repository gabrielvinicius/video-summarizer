import pytest
from fastapi.testclient import TestClient
from main import app
from src.auth.api.dependencies import get_auth_service
from src.auth.infrastructure.user_repository import InMemoryUserRepository

client = TestClient(app)

@pytest.mark.asyncio
async def test_full_video_summary_flow():
    # Registra um usuário
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    user_id = response.json()["id"]

    # Login
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "securepassword123"
    })
    token = response.json()["access_token"]

    # Upload de vídeo
    with open("tests/sample.mp4", "rb") as file:
        response = client.post(
            "/videos/upload",
            files={"file": file},
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    video_id = response.json()["video_id"]

    # Verifica o status do vídeo (polling ou mock de eventos)
    response = client.get(f"/videos/{video_id}")
    assert response.json()["status"] == "COMPLETED"

    # Verifica o resumo
    response = client.get(f"/summaries/{video_id}")
    assert response.status_code == 200
    assert len(response.json()["summary"]) > 0

    # Verifica a notificação (mock SMTP)
    response = client.get(f"/notifications?user_id={user_id}")
    assert any(n["type"] == "EMAIL" for n in response.json())