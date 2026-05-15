from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.features.notification.repository import NotificationRepository
from app.features.parent_portal.schema import (
    ParentOverviewResponse,
    ParentStudentProfile,
    ParentWalletOverview,
)
from app.features.student.repository import StudentRepository
from app.features.transaction.repository import TransactionRepository
from app.features.user.model import User
from app.features.wallet.repository import WalletRepository


class ParentPortalService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repo = StudentRepository(db)
        self.wallet_repo = WalletRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.notification_repo = NotificationRepository(db)

    def get_overview(self, parent_user: User) -> ParentOverviewResponse:
        student = self.student_repo.get_by_parent_user_id(parent_user.id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found for parent")

        wallet = self.wallet_repo.get_by_student_id(student.id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        transactions = self.tx_repo.list_for_student(student.id)[:20]
        notifications = self.notification_repo.list_for_student(student.id)[:20]
        today_spent = self.tx_repo.sum_today_purchases(student.id)
        daily_limit = wallet.daily_spending_limit
        remaining_daily_limit = None
        if daily_limit is not None and daily_limit > 0:
            remaining_daily_limit = max(float(daily_limit) - today_spent, 0.0)

        return ParentOverviewResponse(
            parent_name=parent_user.full_name,
            parent_username=parent_user.username,
            student=ParentStudentProfile(
                student_id=student.id,
                full_name=student.full_name,
                student_code=student.student_code,
                stage=student.grade,
                grade_level=student.classroom,
                national_id=student.national_id,
                photo_url=student.photo_url,
                blood_type=student.blood_type,
                has_chronic_disease=student.has_chronic_disease,
                chronic_disease_details=student.chronic_disease_details,
                qr_code_data=student.qr_code_data,
                card_expiry_year=student.card_expiry_year,
                card_issued_at=student.card_issued_at,
                card_issued_by=student.card_issued_by,
                card_issue_count=student.card_issue_count,
            ),
            wallet=ParentWalletOverview(
                balance=float(wallet.balance),
                daily_spending_limit=float(daily_limit) if daily_limit is not None else None,
                today_spent=today_spent,
                remaining_daily_limit=remaining_daily_limit,
            ),
            transactions=transactions,
            notifications=notifications,
        )

    def update_daily_limit(self, parent_user: User, daily_spending_limit: float | None) -> ParentWalletOverview:
        student = self.student_repo.get_by_parent_user_id(parent_user.id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found for parent")

        wallet = self.wallet_repo.get_by_student_id(student.id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        normalized_limit = None
        if daily_spending_limit is not None and daily_spending_limit > 0:
            normalized_limit = float(daily_spending_limit)

        wallet.daily_spending_limit = normalized_limit
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)

        today_spent = self.tx_repo.sum_today_purchases(student.id)
        remaining_daily_limit = None
        if wallet.daily_spending_limit is not None and wallet.daily_spending_limit > 0:
            remaining_daily_limit = max(float(wallet.daily_spending_limit) - today_spent, 0.0)

        return ParentWalletOverview(
            balance=float(wallet.balance),
            daily_spending_limit=(
                float(wallet.daily_spending_limit)
                if wallet.daily_spending_limit is not None
                else None
            ),
            today_spent=today_spent,
            remaining_daily_limit=remaining_daily_limit,
        )

    def update_device_token(self, parent_user: User, device_token: str) -> None:
        current_settings = dict(parent_user.settings or {})
        current_settings["fcm_device_token"] = device_token.strip()
        parent_user.settings = current_settings
        self.db.add(parent_user)
        self.db.commit()

    def change_password(self, parent_user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, parent_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الحالية غير صحيحة",
            )
        if current_password == new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="كلمة المرور الجديدة يجب أن تكون مختلفة عن الحالية",
            )

        parent_user.password_hash = get_password_hash(new_password)
        self.db.add(parent_user)
        self.db.commit()
