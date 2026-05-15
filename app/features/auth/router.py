from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.features.auth.schema import (
    CurrentUserResponse,
    LoginRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    TokenResponse,
)
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload.username, payload.password)


@router.get("/me", response_model=CurrentUserResponse)
def me(user=Depends(get_current_user)):
    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
    )


@router.post("/change-password", response_model=PasswordChangeResponse)
def change_password(
    payload: PasswordChangeRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).change_password(user, payload.current_password, payload.new_password)
    return PasswordChangeResponse()
