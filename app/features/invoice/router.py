from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.invoice.schema import InvoiceCreate, InvoiceRead
from app.features.invoice.service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceRead)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return InvoiceService(db).create(payload, cashier_id=user.id)


@router.get("/", response_model=list[InvoiceRead])
def list_invoices(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return InvoiceService(db).list_all()
