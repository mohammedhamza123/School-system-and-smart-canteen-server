from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.wallet.schema import WalletRead, WalletRechargeRequest
from app.features.wallet.service import WalletService

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/student/{student_id}", response_model=WalletRead)
def get_wallet(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.FINANCE,
            UserRole.CARD_ISSUER,
            UserRole.CANTEEN_STAFF,
        )
    ),
):
    return WalletService(db).get_wallet(student_id)


@router.post("/student/{student_id}/recharge", response_model=WalletRead)
def recharge_wallet(
    student_id: int,
    payload: WalletRechargeRequest,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.ADMIN, UserRole.FINANCE, UserRole.CARD_ISSUER)),
):
    return WalletService(db).recharge(
        student_id=student_id,
        amount=payload.amount,
        operator_id=user.id,
        note=payload.note,
    )
