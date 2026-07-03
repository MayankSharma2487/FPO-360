from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token
)
from app.services.auth_service import AuthService
from app.auth.dependencies import get_current_user
from app.models.user import User
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    return service.register_user(user)


@router.post("/login", response_model=Token)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    db_user = service.authenticate_user(user)
    token = service.create_token(db_user)

    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/token", response_model=Token)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    login_data = UserLogin(
        email=form_data.username,
        password=form_data.password
    )

    db_user = service.authenticate_user(login_data)

    token = service.create_token(db_user)

    return Token(
        access_token=token,
        token_type="bearer"
    )