import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app  # Importe sua aplicação FastAPI

client = TestClient(app)

@pytest.mark.asyncio
async def test_register_user(db: Session):
    # Teste de registro válido
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

    # Teste de email duplicado
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "anotherpassword"
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login(db: Session):
    # Primeiro registre um usuário
    client.post("/auth/register", json={
        "email": "login@test.com",
        "password": "validpass"
    })

    # Login válido
    response = client.post("/auth/login", data={
        "username": "login@test.com",
        "password": "validpass"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Senha inválida
    response = client.post("/auth/login", data={
        "username": "login@test.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401