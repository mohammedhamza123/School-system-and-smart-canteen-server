from datetime import datetime

from pydantic import BaseModel, Field

from app.features.notification.schema import NotificationRead
from app.features.transaction.schema import TransactionRead


class ParentStudentProfile(BaseModel):
    student_id: int
    full_name: str
    student_code: str
    stage: str
    grade_level: str
    national_id: str | None
    photo_url: str | None
    blood_type: str | None
    has_chronic_disease: bool
    chronic_disease_details: str | None
    qr_code_data: str
    card_expiry_year: int
    card_issued_at: datetime | None
    card_issued_by: str | None
    card_issue_count: int


class ParentWalletOverview(BaseModel):
    balance: float
    daily_spending_limit: float | None = None
    today_spent: float = 0
    remaining_daily_limit: float | None = None


class ParentOverviewResponse(BaseModel):
    parent_name: str
    parent_username: str
    student: ParentStudentProfile
    wallet: ParentWalletOverview
    transactions: list[TransactionRead]
    notifications: list[NotificationRead]


class ParentDailyLimitUpdateRequest(BaseModel):
    daily_spending_limit: float | None = Field(default=None, ge=0)


class ParentDeviceTokenUpdateRequest(BaseModel):
    device_token: str = Field(min_length=16, max_length=500)


class ParentDeviceTokenUpdateResponse(BaseModel):
    success: bool = True


class ParentPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ParentPasswordChangeResponse(BaseModel):
    success: bool = True
