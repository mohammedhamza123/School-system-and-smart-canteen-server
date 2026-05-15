from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    national_id: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    grade: Mapped[str] = mapped_column(String(50))
    classroom: Mapped[str] = mapped_column(String(50))
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    has_chronic_disease: Mapped[bool] = mapped_column(Boolean, default=False)
    chronic_disease_details: Mapped[str | None] = mapped_column(String(300), nullable=True)
    parent_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    qr_code_data: Mapped[str] = mapped_column(String(500))
    card_expiry_year: Mapped[int] = mapped_column(Integer)
    card_issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    card_issued_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    card_issue_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def stage(self) -> str:
        return self.grade

    @property
    def grade_level(self) -> str:
        return self.classroom
