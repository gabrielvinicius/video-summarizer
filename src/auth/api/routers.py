from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..application.auth_service import AuthService
from dependencies import get_auth_service, get_current_user
from schemas import Token, UserResponse, UserCreate
from ..domain.user import User
from ..infrastructure.user_repository import UserRepository
from ...shared.infrastructure.database import get_db

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(UserRepository(db))
    try:
        user = auth_service.create_user(user_data.email, user_data.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_service: AuthService = Depends(get_auth_service)  # AuthService injetado
):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    token = auth_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):  # Usuário autenticado
    return current_user

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)  # Somente admin
):
    users = db.query(User).all()
    return users