# src/auth/api/routers.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.api.dependencies import get_auth_service, get_current_user, get_current_admin_user
from src.auth.api.schemas import Token, UserResponse, UserCreate, LoginJSON
from src.auth.application.auth_service import AuthService
from src.auth.domain.user import User

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)  # Correct dependency injection
):
    """Registers a new user."""
    try:
        user = await auth_service.create_user(user_data.email, user_data.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login_json(
        login_data: LoginJSON,
        auth_service: AuthService = Depends(get_auth_service)
):
    """Logs a user in using JSON credentials."""
    user = await auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"  # Translated message
        )
    token = auth_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/token", response_model=Token, include_in_schema=False) # Changed path to /token for clarity
async def login_form(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_service: AuthService = Depends(get_auth_service)
):
    """Logs a user in using form data (for OAuth2 compatible clients)."""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"  # Translated message
        )
    token = auth_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Retrieves the currently authenticated user's details."""
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
        auth_service: AuthService = Depends(get_auth_service), # Correct dependency injection
        _: User = Depends(get_current_admin_user) # Ensures only admins can access
):
    """Lists all users in the system (admin only)."""
    users = await auth_service.list_all_users() # Use the service method
    return users
