from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    student_id: int | None = None
    title: str
    body: str
    is_important: bool = False


class NotificationRead(BaseModel):
    id: int
    student_id: int | None
    title: str
    body: str
    is_important: bool
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
