from sqlalchemy.orm import Session

from app.features.transaction.repository import TransactionRepository


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.repo = TransactionRepository(db)

    def list_student_transactions(self, student_id: int):
        return self.repo.list_for_student(student_id)
