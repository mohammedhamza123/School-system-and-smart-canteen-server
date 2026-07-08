from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.security import get_password_hash
from app.features.student.model import Student
from app.features.student.repository import StudentRepository
from app.features.student.schema import (
    ALLOWED_GRADE_LEVELS,
    EducationStage,
    GradeLevelStat,
    StageStat,
    StudentCardRenewRequest,
    StudentCreate,
    StudentRead,
    StudentStatisticsReport,
    StudentUpdate,
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

    def list_students_read(self, national_id: str | None = None) -> list[StudentRead]:
        students = self.list_students(national_id=national_id)
        return [self._to_student_read(student) for student in students]

    def _to_student_read(self, student: Student) -> StudentRead:
        parent = self.user_repo.get_by_id(student.parent_user_id)
        student_data = StudentRead.model_validate(student).model_dump()
        student_data["parent_username"] = parent.username if parent else None
        student_data["parent_full_name"] = parent.full_name if parent else None
        return StudentRead(**student_data)

    def update_student(self, student_id: int, payload: StudentUpdate) -> StudentRead:
        student = self.student_repo.get_by_id(student_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields to update",
            )

        next_stage = payload.stage.value if payload.stage is not None else student.grade
        next_grade_level = (
            payload.grade_level if payload.grade_level is not None else student.classroom
        )
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

        next_has_chronic = (
            payload.has_chronic_disease
            if payload.has_chronic_disease is not None
            else student.has_chronic_disease
        )
        next_chronic_details = (
            payload.chronic_disease_details
            if payload.chronic_disease_details is not None
            else student.chronic_disease_details
        )
        if next_has_chronic and not next_chronic_details:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Chronic disease details are required",
            )

        if payload.national_id is not None:
            existing = self.student_repo.get_by_national_id(payload.national_id)
            if existing is not None and existing.id != student.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="National ID already exists",
                )
            student.national_id = payload.national_id

        if payload.full_name is not None:
            student.full_name = payload.full_name
        if payload.stage is not None:
            student.grade = payload.stage.value
        if payload.grade_level is not None:
            student.classroom = payload.grade_level
        if payload.photo_url is not None:
            student.photo_url = payload.photo_url
        if payload.blood_type is not None:
            student.blood_type = payload.blood_type.value
        if payload.has_chronic_disease is not None:
            student.has_chronic_disease = payload.has_chronic_disease
        if payload.chronic_disease_details is not None:
            student.chronic_disease_details = payload.chronic_disease_details
        elif payload.has_chronic_disease is False:
            student.chronic_disease_details = None

        student = self.student_repo.save(student)
        return self._to_student_read(student)

    def get_statistics_report(self) -> StudentStatisticsReport:
        students = self.student_repo.list_all()
        counts: dict[str, dict[str, int]] = {
            stage.value: {grade: 0 for grade in ALLOWED_GRADE_LEVELS[stage]}
            for stage in EducationStage
        }

        chronic_count = 0
        cards_issued = 0
        for student in students:
            stage_counts = counts.setdefault(student.grade, {})
            stage_counts[student.classroom] = stage_counts.get(student.classroom, 0) + 1
            if student.has_chronic_disease:
                chronic_count += 1
            if student.card_issued_at is not None:
                cards_issued += 1

        stages: list[StageStat] = []
        for stage in EducationStage:
            grade_counts = counts.get(stage.value, {})
            ordered_grades = [
                GradeLevelStat(grade_level=grade, count=grade_counts.get(grade, 0))
                for grade in sorted(ALLOWED_GRADE_LEVELS[stage])
            ]
            stage_total = sum(item.count for item in ordered_grades)
            stages.append(
                StageStat(stage=stage.value, count=stage_total, grades=ordered_grades)
            )

        return StudentStatisticsReport(
            total_students=len(students),
            chronic_disease_count=chronic_count,
            cards_issued_count=cards_issued,
            stages=stages,
            generated_at=datetime.utcnow(),
        )

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

    def reset_parent_password(
        self,
        student_id: int,
        new_password: str | None = None,
    ) -> tuple[Student, str, str]:
        student = self.student_repo.get_by_id(student_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )

        parent = self.user_repo.get_by_id(student.parent_user_id)
        if parent is None or parent.role != UserRole.PARENT.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent account not found",
            )

        password = new_password.strip() if new_password and new_password.strip() else generate_parent_password()
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password must be at least 8 characters",
            )

        parent.password_hash = get_password_hash(password)
        self.user_repo.save(parent)
        return student, parent.username, password

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
