from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.user.schema import AdminSettings, AdminSettingsUpdate, UserCreate, UserRead
from app.features.user.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return UserService(db).create_user(payload)


@router.get("/", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return UserService(db).list_users()


@router.get("/admin/settings", response_model=AdminSettings)
def get_admin_settings(
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles(UserRole.ADMIN)),
):
    return UserService(db).get_admin_settings(admin_user.id)


@router.put("/admin/settings", response_model=AdminSettings)
def update_admin_settings(
    payload: AdminSettingsUpdate,
    db: Session = Depends(get_db),
    admin_user=Depends(require_roles(UserRole.ADMIN)),
):
    return UserService(db).update_admin_settings(admin_user.id, payload)
