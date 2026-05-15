from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import get_password_hash
from app.features.student.model import Student
from app.features.student.repository import StudentRepository
from app.features.student.schema import (
    ALLOWED_GRADE_LEVELS,
    StudentCardRenewRequest,
    StudentCreate,
)
from app.features.student.utils import (
    generate_parent_password,
    generate_student_code,
    generate_student_qr_base64,
)
from app.features.user.model import User
from app.features.user.repository import UserRepository
from app.features.wallet.model import Wallet
from app.features.wallet.repository import WalletRepository


class StudentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.student_repo = StudentRepository(db)
        self.user_repo = UserRepository(db)
        self.wallet_repo = WalletRepository(db)

    def create_student(self, payload: StudentCreate) -> tuple[Student, str, str]:
        student_code = payload.student_code.strip() if payload.student_code else ""
        if not student_code:
            student_code = self._generate_unique_student_code()
        elif self.student_repo.get_by_code(student_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student code already exists",
            )

        if self.student_repo.get_by_national_id(payload.national_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="National ID already exists",
            )

        parent_username = self._normalize_parent_username(
            payload.parent_username,
            payload.national_id,
        )
        if self.user_repo.get_by_username(parent_username):
            parent_username = self._generate_available_parent_username(parent_username)

        temp_password = generate_parent_password()
        parent_name = payload.parent_name or f"ولي أمر {payload.full_name}"
        parent_user = User(
            username=parent_username,
            full_name=parent_name,
            password_hash=get_password_hash(temp_password),
            role=UserRole.PARENT.value,
        )
        self.db.add(parent_user)
        self.db.flush()

        student = Student(
            student_code=student_code,
            full_name=payload.full_name,
            national_id=payload.national_id,
            grade=payload.stage.value,
            classroom=payload.grade_level,
            photo_url=payload.photo_url,
            blood_type=payload.blood_type.value,
            has_chronic_disease=payload.has_chronic_disease,
            chronic_disease_details=payload.chronic_disease_details,
            parent_user_id=parent_user.id,
            qr_code_data=generate_student_qr_base64(student_code),
            card_expiry_year=datetime.utcnow().year + 1,
        )
        self.db.add(student)
        self.db.flush()

        self.db.add(Wallet(student_id=student.id, balance=0))
        self.db.commit()
        self.db.refresh(student)
        return student, parent_username, temp_password

    def list_students(self, national_id: str | None = None) -> list[Student]:
        return self.student_repo.list_all(national_id=national_id)

    def get_card(self, student_id: int) -> Student:
        student = self.student_repo.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        return student

    def get_wallet_balance(self, student_id: int) -> float:
        wallet = self.wallet_repo.get_by_student_id(student_id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        return float(wallet.balance)

    def list_issued_cards(self) -> list[Student]:
        return self.student_repo.list_issued_cards()

    def issue_card(self, student_id: int, issuer_name: str) -> Student:
        student = self.get_card(student_id)
        student.card_issued_at = datetime.utcnow()
        student.card_issued_by = issuer_name
        student.card_issue_count = (student.card_issue_count or 0) + 1
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def renew_card(
        self,
        student_id: int,
        payload: StudentCardRenewRequest,
        issuer_name: str,
    ) -> Student:
        student = self.get_card(student_id)

        next_stage = payload.stage.value if payload.stage is not None else student.grade
        next_grade_level = payload.grade_level or student.classroom
        stage_key = payload.stage
        if stage_key is None:
            for stage, grades in ALLOWED_GRADE_LEVELS.items():
                if stage.value == next_stage:
                    stage_key = stage
                    break

        if stage_key is not None:
            allowed_grades = ALLOWED_GRADE_LEVELS.get(stage_key, set())
            if next_grade_level not in allowed_grades:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Grade level does not match selected stage",
                )

        student.grade = next_stage
        student.classroom = next_grade_level
        student.card_expiry_year = payload.card_expiry_year or (datetime.utcnow().year + 1)
        student.card_issued_at = datetime.utcnow()
        student.card_issued_by = issuer_name
        student.card_issue_count = (student.card_issue_count or 0) + 1
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)
        return student

    def _generate_unique_student_code(self) -> str:
        for _ in range(20):
            candidate = generate_student_code()
            if self.student_repo.get_by_code(candidate) is None:
                return candidate
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique student code",
        )

    def _normalize_parent_username(self, username: str | None, national_id: str) -> str:
        if username and username.strip():
            return username.strip()
        fallback = national_id[-6:] if len(national_id) >= 6 else national_id
        return f"parent_{fallback}"

    def _generate_available_parent_username(self, base_username: str) -> str:
        for _ in range(20):
            suffix = generate_parent_password(4).lower()
            candidate = f"{base_username}_{suffix}"
            if self.user_repo.get_by_username(candidate) is None:
                return candidate
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate unique parent username",
        )
