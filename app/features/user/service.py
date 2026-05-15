from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import get_password_hash
from app.features.user.model import User
from app.features.user.repository import UserRepository
from app.features.user.schema import AdminSettings, AdminSettingsUpdate, UserCreate


DEFAULT_ADMIN_SETTINGS = AdminSettings().model_dump()


class UserService:
    def __init__(self, db: Session) -> None:
        self.repo = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        exists = self.repo.get_by_username(payload.username)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        settings: dict = {}
        if payload.role == UserRole.ADMIN:
            settings = DEFAULT_ADMIN_SETTINGS.copy()

        user = User(
            username=payload.username,
            full_name=payload.full_name,
            password_hash=get_password_hash(payload.password),
            role=payload.role.value,
            settings=settings,
        )
        return self.repo.create(user)

    def list_users(self) -> list[User]:
        return self.repo.list_all()

    def get_admin_settings(self, admin_user_id: int) -> dict:
        admin_user = self.repo.get_by_id(admin_user_id)
        if admin_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return self._normalize_admin_settings(admin_user.settings)

    def update_admin_settings(self, admin_user_id: int, payload: AdminSettingsUpdate) -> dict:
        admin_user = self.repo.get_by_id(admin_user_id)
        if admin_user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        updated_fields = payload.model_dump(exclude_unset=True)
        current = self._normalize_admin_settings(admin_user.settings)
        current.update(updated_fields)
        admin_user.settings = current

        self.repo.save(admin_user)
        return admin_user.settings

    @staticmethod
    def _normalize_admin_settings(settings: object) -> dict:
        merged = DEFAULT_ADMIN_SETTINGS.copy()
        if isinstance(settings, dict):
            merged.update({key: value for key, value in settings.items() if key in merged})
        return merged
