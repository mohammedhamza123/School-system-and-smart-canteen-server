from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.parent_portal.schema import (
    ParentDailyLimitUpdateRequest,
    ParentDeviceTokenUpdateRequest,
    ParentDeviceTokenUpdateResponse,
    ParentOverviewResponse,
    ParentPasswordChangeRequest,
    ParentPasswordChangeResponse,
    ParentWalletOverview,
)
from app.features.parent_portal.service import ParentPortalService

router = APIRouter(prefix="/parents", tags=["parents"])


@router.get("/me/overview", response_model=ParentOverviewResponse)
def get_parent_overview(
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.PARENT)),
):
    return ParentPortalService(db).get_overview(user)


@router.put("/me/daily-limit", response_model=ParentWalletOverview)
def update_parent_daily_limit(
    payload: ParentDailyLimitUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.PARENT)),
):
    return ParentPortalService(db).update_daily_limit(user, payload.daily_spending_limit)


@router.post("/me/device-token", response_model=ParentDeviceTokenUpdateResponse)
def update_parent_device_token(
    payload: ParentDeviceTokenUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.PARENT)),
):
    ParentPortalService(db).update_device_token(user, payload.device_token)
    return ParentDeviceTokenUpdateResponse()


@router.post("/me/change-password", response_model=ParentPasswordChangeResponse)
def change_parent_password(
    payload: ParentPasswordChangeRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.PARENT)),
):
    ParentPortalService(db).change_password(
        user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return ParentPasswordChangeResponse()
