from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class EducationStage(str, Enum):
    PRIMARY = "ابتدائي"
    PREPARATORY = "اعدادي"
    SECONDARY = "ثانوي"


class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


ALLOWED_GRADE_LEVELS: dict[EducationStage, set[str]] = {
    EducationStage.PRIMARY: {
        "الأول الابتدائي",
        "الثاني الابتدائي",
        "الثالث الابتدائي",
        "الرابع الابتدائي",
        "الخامس الابتدائي",
        "السادس الابتدائي",
    },
    EducationStage.PREPARATORY: {
        "السابع",
        "الثامن",
        "التاسع",
    },
    EducationStage.SECONDARY: {
        "الأول الثانوي",
        "الثاني الثانوي",
        "الثالث الثانوي",
    },
}


class StudentCreate(BaseModel):
    student_code: str | None = None
    full_name: str
    stage: EducationStage
    grade_level: str
    national_id: str = Field(min_length=6, max_length=30)
    photo_url: str | None = None
    blood_type: BloodType
    has_chronic_disease: bool = False
    chronic_disease_details: str | None = None
    parent_name: str | None = None
    parent_username: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Full name must be at least 3 characters")
        return cleaned

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, value: str) -> str:
        return value.strip()

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit():
            raise ValueError("National ID must contain digits only")
        return cleaned

    @field_validator("photo_url")
    @classmethod
    def normalize_photo_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("chronic_disease_details")
    @classmethod
    def normalize_chronic_details(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def validate_stage_and_grade(self) -> "StudentCreate":
        allowed_grades = ALLOWED_GRADE_LEVELS.get(self.stage, set())
        if self.grade_level not in allowed_grades:
            raise ValueError("Grade level does not match selected stage")
        if self.has_chronic_disease and not self.chronic_disease_details:
            raise ValueError("Chronic disease details are required")
        return self


class StudentUpdate(BaseModel):
    full_name: str | None = None
    stage: EducationStage | None = None
    grade_level: str | None = None
    national_id: str | None = None
    photo_url: str | None = None
    blood_type: BloodType | None = None
    has_chronic_disease: bool | None = None
    chronic_disease_details: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Full name must be at least 3 characters")
        return cleaned

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned.isdigit():
            raise ValueError("National ID must contain digits only")
        return cleaned

    @field_validator("photo_url")
    @classmethod
    def normalize_photo_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("chronic_disease_details")
    @classmethod
    def normalize_chronic_details(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class GradeLevelStat(BaseModel):
    grade_level: str
    count: int


class StageStat(BaseModel):
    stage: str
    count: int
    grades: list[GradeLevelStat]


class StudentStatisticsReport(BaseModel):
    total_students: int
    chronic_disease_count: int
    cards_issued_count: int
    stages: list[StageStat]
    generated_at: datetime


class StudentRead(BaseModel):
    id: int
    student_code: str
    full_name: str
    stage: str
    grade_level: str
    national_id: str | None
    photo_url: str | None
    blood_type: str | None
    has_chronic_disease: bool
    chronic_disease_details: str | None
    grade: str
    classroom: str
    qr_code_data: str
    card_expiry_year: int
    card_issued_at: datetime | None
    card_issued_by: str | None
    card_issue_count: int
    created_at: datetime
    parent_username: str | None = None
    parent_full_name: str | None = None

    model_config = {"from_attributes": True}


class StudentCardResponse(BaseModel):
    student_name: str
    student_id: int
    student_code: str
    national_id: str | None
    blood_type: str | None
    qr_code_data: str
    wallet_balance: float = 0
    stage: str
    grade_level: str
    card_expiry_year: int
    card_issued_at: datetime | None = None
    card_issued_by: str | None = None
    card_issue_count: int = 0


class IssuedStudentCardRead(BaseModel):
    student_id: int
    student_name: str
    student_code: str
    stage: str
    grade_level: str
    card_expiry_year: int
    card_issued_at: datetime
    card_issued_by: str | None = None
    card_issue_count: int = 0


class StudentCardRenewRequest(BaseModel):
    stage: EducationStage | None = None
    grade_level: str | None = None
    card_expiry_year: int | None = Field(default=None, ge=2024, le=2100)

    @field_validator("grade_level")
    @classmethod
    def normalize_grade_level(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class StudentCreateResponse(BaseModel):
    student: StudentRead
    parent_username: str
    parent_initial_password: str


class ParentPasswordResetRequest(BaseModel):
    new_password: str | None = Field(default=None, min_length=8, max_length=128)


class ParentPasswordResetResponse(BaseModel):
    student_id: int
    student_name: str
    parent_username: str
    new_password: str
