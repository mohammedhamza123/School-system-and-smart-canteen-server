from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.notification.schema import NotificationCreate, NotificationRead
from app.features.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/", response_model=NotificationRead)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.ADMIN)),
):
    return NotificationService(db).create(payload, created_by=user.id)


@router.get("/", response_model=list[NotificationRead])
def list_notifications(
    student_id: int | None = None,
    db: Session = Depends(get_db),
    _: dict = Depends(
        require_roles(UserRole.ADMIN, UserRole.STUDENT_MANAGER, UserRole.CANTEEN_STAFF)
    ),
):
    return NotificationService(db).list_for_student(student_id)
