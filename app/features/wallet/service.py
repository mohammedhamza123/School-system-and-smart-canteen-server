from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.common.enums import TransactionType
from app.core.firebase_push import FirebasePushService
from app.features.notification.model import Notification
from app.features.student.repository import StudentRepository
from app.features.transaction.model import Transaction
from app.features.transaction.repository import TransactionRepository
from app.features.wallet.model import Wallet
from app.features.wallet.repository import WalletRepository


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.student_repo = StudentRepository(db)

    def get_wallet(self, student_id: int) -> Wallet:
        wallet = self.wallet_repo.get_by_student_id(student_id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        return wallet

    def recharge(self, student_id: int, amount: float, operator_id: int, note: str | None = None) -> Wallet:
        wallet = self.get_wallet(student_id)
        student = self.student_repo.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        balance_before = wallet.balance
        balance_after = balance_before + amount

        self.db.execute(
            update(Wallet).where(Wallet.student_id == student_id).values(balance=Wallet.balance + amount)
        )
        self.db.flush()
        tx = Transaction(
            student_id=student_id,
            transaction_type=TransactionType.RECHARGE.value,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            created_by=operator_id,
            note=note,
        )
        self.tx_repo.create(tx)
        self.db.add(
            Notification(
                student_id=student_id,
                title="تم شحن البطاقة",
                body=(
                    f"تم شحن بطاقة الطالب {student.full_name} بمبلغ {amount:.2f}. "
                    f"الرصيد الحالي {balance_after:.2f}."
                ),
                is_important=True,
                created_by=operator_id,
            )
        )
        self.db.commit()
        self.db.refresh(wallet)
        FirebasePushService(self.db).send_to_parent(
            student_id=student_id,
            title="تم شحن البطاقة",
            body=(
                f"تم شحن بطاقة الطالب {student.full_name} بمبلغ {amount:.2f}. "
                f"الرصيد الحالي {balance_after:.2f}."
            ),
            data={
                "type": "recharge",
                "screen": "notifications",
                "student_id": student_id,
            },
        )
        return wallet
