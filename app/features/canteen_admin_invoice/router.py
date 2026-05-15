from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.features.canteen_admin_invoice.schema import CanteenAdminInvoiceCreate, CanteenAdminInvoiceRead
from app.features.canteen_admin_invoice.service import CanteenAdminInvoiceService

router = APIRouter(prefix="/canteen-admin/invoices", tags=["canteen-admin-invoices"])


@router.post("/post", response_model=CanteenAdminInvoiceRead)
def create_and_post_invoice(
    payload: CanteenAdminInvoiceCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return CanteenAdminInvoiceService(db).create_posted(payload, created_by=user.id)


@router.get("/", response_model=list[CanteenAdminInvoiceRead])
def list_posted_invoices(
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN, UserRole.CANTEEN_STAFF)),
):
    return CanteenAdminInvoiceService(db).list_all(category=category)
