from sqlalchemy.orm import Session

from app.features.notification.model import Notification


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_for_student(self, student_id: int | None = None) -> list[Notification]:
        query = self.db.query(Notification)
        if student_id is not None:
            query = query.filter((Notification.student_id == student_id) | (Notification.student_id.is_(None)))
        return query.order_by(Notification.id.desc()).all()
