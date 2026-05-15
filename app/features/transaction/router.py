from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.transaction.schema import TransactionRead
from app.features.transaction.service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/student/{student_id}", response_model=list[TransactionRead])
def list_transactions_for_student(
    student_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(
        require_roles(UserRole.ADMIN, UserRole.FINANCE, UserRole.CANTEEN_STAFF)
    ),
):
    return TransactionService(db).list_student_transactions(student_id)
