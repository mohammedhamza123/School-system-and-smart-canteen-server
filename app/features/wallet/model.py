from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), unique=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    daily_spending_limit: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
