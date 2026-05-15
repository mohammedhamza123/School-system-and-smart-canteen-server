from sqlalchemy.orm import Session

from app.core.firebase_push import FirebasePushService
from app.features.notification.model import Notification
from app.features.notification.repository import NotificationRepository
from app.features.notification.schema import NotificationCreate


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = NotificationRepository(db)

    def create(self, payload: NotificationCreate, created_by: int) -> Notification:
        notification = self.repo.create(
            Notification(**payload.model_dump(), created_by=created_by)
        )
        if notification.student_id is not None:
            FirebasePushService(self.db).send_to_parent(
                student_id=notification.student_id,
                title=notification.title,
                body=notification.body,
                data={
                    "type": "parent_call",
                    "screen": "notifications",
                    "student_id": notification.student_id,
                },
            )
        return notification

    def list_for_student(self, student_id: int | None = None):
        return self.repo.list_for_student(student_id)
