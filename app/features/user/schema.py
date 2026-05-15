from datetime import datetime

from pydantic import BaseModel

from app.common.enums import UserRole


class AdminSettings(BaseModel):
    school_name: str = "My School"
    school_code: str = "MMS"
    currency: str = "SAR"
    timezone: str = "Asia/Riyadh"
    allow_negative_wallet: bool = False
    low_balance_alert_threshold: float = 10.0
    enable_parent_notifications: bool = True


class AdminSettingsUpdate(BaseModel):
    school_name: str | None = None
    school_code: str | None = None
    currency: str | None = None
    timezone: str | None = None
    allow_negative_wallet: bool | None = None
    low_balance_alert_threshold: float | None = None
    enable_parent_notifications: bool | None = None


class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    settings: dict
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
