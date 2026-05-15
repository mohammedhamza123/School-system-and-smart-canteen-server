from __future__ import annotations

import logging
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.features.student.repository import StudentRepository
from app.features.user.repository import UserRepository

logger = logging.getLogger(__name__)


class FirebasePushService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repo = StudentRepository(db)
        self.user_repo = UserRepository(db)

    def send_to_parent(
        self,
        *,
        student_id: int,
        title: str,
        body: str,
        data: dict[str, str | int | float | bool | None] | None = None,
    ) -> bool:
        app = self._get_app()
        if app is None:
            return False

        student = self.student_repo.get_by_id(student_id)
        if student is None:
            return False

        parent_user = self.user_repo.get_by_id(student.parent_user_id)
        if parent_user is None:
            logger.warning("Push skipped: parent user not found for student_id=%s", student_id)
            return False

        device_token = str((parent_user.settings or {}).get("fcm_device_token", "")).strip()
        if not device_token:
            logger.warning("Push skipped: missing device token for parent user_id=%s", parent_user.id)
            return False

        payload = {
            key: str(value)
            for key, value in (data or {}).items()
            if value is not None
        }
        payload.setdefault("student_id", str(student_id))

        message = messaging.Message(
            token=device_token,
            notification=messaging.Notification(title=title, body=body),
            data=payload,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(channel_id="parent_alerts"),
            ),
        )

        try:
            response = messaging.send(message, app=app)
            logger.info(
                "Firebase push sent successfully: student_id=%s parent_user_id=%s message_id=%s",
                student_id,
                parent_user.id,
                response,
            )
            return True
        except Exception:
            logger.exception(
                "Failed to send Firebase push notification for student_id=%s parent_user_id=%s",
                student_id,
                parent_user.id,
            )
            return False

    def _get_app(self):
        if not settings.firebase_notifications_enabled:
            return None

        credentials_path = settings.firebase_credentials_path
        if not credentials_path:
            logger.warning("Firebase credentials path is not configured")
            return None

        credentials_file = Path(credentials_path)
        if not credentials_file.exists():
            logger.warning("Firebase credentials file was not found: %s", credentials_file)
            return None

        try:
            return firebase_admin.get_app()
        except ValueError:
            try:
                app = firebase_admin.initialize_app(
                    credentials.Certificate(str(credentials_file))
                )
                logger.info("Firebase Admin SDK initialized using %s", credentials_file)
                return app
            except Exception:
                logger.exception("Failed to initialize Firebase Admin SDK")
                return None
