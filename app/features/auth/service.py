from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.features.auth.schema import TokenResponse
from app.features.user.model import User
from app.features.user.repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def login(self, username: str, password: str) -> TokenResponse:
        user = self.user_repo.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        token = create_access_token(subject=str(user.id), extra={"role": user.role})
        return TokenResponse(access_token=token)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الحالية غير صحيحة",
            )
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="يجب أن تختلف كلمة المرور الجديدة عن الحالية",
            )
        user.password_hash = get_password_hash(new_password)
        self.user_repo.save(user)
