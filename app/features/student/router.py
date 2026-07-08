from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.student.schema import (
    IssuedStudentCardRead,
    ParentPasswordResetRequest,
    ParentPasswordResetResponse,
    StudentCardRenewRequest,
    StudentCardResponse,
    StudentCreate,
    StudentCreateResponse,
    StudentRead,
    StudentStatisticsReport,
    StudentUpdate,
)
from app.features.student.service import StudentService

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentCreateResponse)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.STUDENT_MANAGER)),
):
    student, parent_username, temp_password = StudentService(db).create_student(payload)
    service = StudentService(db)
    return StudentCreateResponse(
        student=service._to_student_read(student),
        parent_username=parent_username,
        parent_initial_password=temp_password,
    )


@router.get("/", response_model=list[StudentRead])
def list_students(
    national_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.STUDENT_MANAGER, UserRole.CARD_ISSUER)),
):
    return StudentService(db).list_students_read(national_id=national_id)


@router.get("/statistics", response_model=StudentStatisticsReport)
def get_student_statistics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return StudentService(db).get_statistics_report()


@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.STUDENT_MANAGER)),
):
    return StudentService(db).update_student(student_id, payload)


@router.post("/{student_id}/parent/reset-password", response_model=ParentPasswordResetResponse)
def reset_parent_password(
    student_id: int,
    payload: ParentPasswordResetRequest = ParentPasswordResetRequest(),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.STUDENT_MANAGER)),
):
    student, parent_username, new_password = StudentService(db).reset_parent_password(
        student_id=student_id,
        new_password=payload.new_password,
    )
    return ParentPasswordResetResponse(
        student_id=student.id,
        student_name=student.full_name,
        parent_username=parent_username,
        new_password=new_password,
    )


@router.get("/{student_id}/card", response_model=StudentCardResponse)
def get_student_card(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CARD_ISSUER)),
):
    service = StudentService(db)
    student = service.get_card(student_id)
    return StudentCardResponse(
        student_id=student.id,
        student_name=student.full_name,
        student_code=student.student_code,
        national_id=student.national_id,
        blood_type=student.blood_type,
        qr_code_data=student.qr_code_data,
        wallet_balance=service.get_wallet_balance(student.id),
        stage=student.grade,
        grade_level=student.classroom,
        card_expiry_year=student.card_expiry_year,
        card_issued_at=student.card_issued_at,
        card_issued_by=student.card_issued_by,
        card_issue_count=student.card_issue_count,
    )


@router.get("/cards/issued", response_model=list[IssuedStudentCardRead])
def list_issued_cards(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CARD_ISSUER)),
):
    students = StudentService(db).list_issued_cards()
    return [
        IssuedStudentCardRead(
            student_id=student.id,
            student_name=student.full_name,
            student_code=student.student_code,
            stage=student.grade,
            grade_level=student.classroom,
            card_expiry_year=student.card_expiry_year,
            card_issued_at=student.card_issued_at,
            card_issued_by=student.card_issued_by,
            card_issue_count=student.card_issue_count,
        )
        for student in students
        if student.card_issued_at is not None
    ]


@router.post("/{student_id}/card/issue", response_model=StudentCardResponse)
def issue_student_card(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.CARD_ISSUER)),
):
    service = StudentService(db)
    student = service.issue_card(student_id, current_user.full_name)
    return StudentCardResponse(
        student_id=student.id,
        student_name=student.full_name,
        student_code=student.student_code,
        national_id=student.national_id,
        blood_type=student.blood_type,
        qr_code_data=student.qr_code_data,
        wallet_balance=service.get_wallet_balance(student.id),
        stage=student.grade,
        grade_level=student.classroom,
        card_expiry_year=student.card_expiry_year,
        card_issued_at=student.card_issued_at,
        card_issued_by=student.card_issued_by,
        card_issue_count=student.card_issue_count,
    )


@router.post("/{student_id}/card/renew", response_model=StudentCardResponse)
def renew_student_card(
    student_id: int,
    payload: StudentCardRenewRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(UserRole.ADMIN, UserRole.CARD_ISSUER)),
):
    service = StudentService(db)
    student = service.renew_card(
        student_id=student_id,
        payload=payload,
        issuer_name=current_user.full_name,
    )
    return StudentCardResponse(
        student_id=student.id,
        student_name=student.full_name,
        student_code=student.student_code,
        national_id=student.national_id,
        blood_type=student.blood_type,
        qr_code_data=student.qr_code_data,
        wallet_balance=service.get_wallet_balance(student.id),
        stage=student.grade,
        grade_level=student.classroom,
        card_expiry_year=student.card_expiry_year,
        card_issued_at=student.card_issued_at,
        card_issued_by=student.card_issued_by,
        card_issue_count=student.card_issue_count,
    )
