# tests/unit/auth/test_auth_service.py
import pytest
from src.auth.application.auth_service import AuthService
from src.auth.infrastructure.user_repository import UserRepository
from src.shared.dependencies import get_user_repository


def test_create_user():
    # Configuração
    user_repo = get_user_repository()
    auth_service = AuthService(user_repo)

    # Execução
    user = auth_service.create_user("user@test.com", "senha123")

    # Verificação
    assert user.email == "user@test.com"
    # assert user.id == "fixed-id"
    assert len(user_repo.find_by_email(user.email)) == 1