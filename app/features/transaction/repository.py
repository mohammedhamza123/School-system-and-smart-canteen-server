from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.enums import TransactionType

from app.features.transaction.model import Transaction


class TransactionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, tx: Transaction) -> Transaction:
        self.db.add(tx)
        self.db.flush()
        return tx

    def list_for_student(self, student_id: int) -> list[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.student_id == student_id)
            .order_by(Transaction.id.desc())
            .all()
        )

    def sum_today_purchases(self, student_id: int) -> float:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        total = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
            .filter(
                Transaction.student_id == student_id,
                Transaction.transaction_type == TransactionType.PURCHASE.value,
                Transaction.created_at >= start,
                Transaction.created_at < end,
            )
            .scalar()
        )
        return float(total or 0.0)
