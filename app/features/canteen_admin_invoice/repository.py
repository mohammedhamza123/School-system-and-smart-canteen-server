from sqlalchemy.orm import Session

from app.features.canteen_admin_invoice.model import CanteenAdminInvoice, CanteenAdminInvoiceItem


class CanteenAdminInvoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_invoice(
        self,
        invoice: CanteenAdminInvoice,
        items: list[CanteenAdminInvoiceItem],
    ) -> CanteenAdminInvoice:
        self.db.add(invoice)
        self.db.flush()
        for item in items:
            item.invoice_id = invoice.id
            self.db.add(item)
        self.db.flush()
        return invoice

    def list_all(self) -> list[CanteenAdminInvoice]:
        return (
            self.db.query(CanteenAdminInvoice)
            .order_by(CanteenAdminInvoice.id.desc())
            .all()
        )

    def list_by_category(self, category: str) -> list[CanteenAdminInvoice]:
        return (
            self.db.query(CanteenAdminInvoice)
            .filter(CanteenAdminInvoice.category == category)
            .order_by(CanteenAdminInvoice.id.desc())
            .all()
        )

    def get_items(self, invoice_id: int) -> list[CanteenAdminInvoiceItem]:
        return (
            self.db.query(CanteenAdminInvoiceItem)
            .filter(CanteenAdminInvoiceItem.invoice_id == invoice_id)
            .order_by(CanteenAdminInvoiceItem.id.asc())
            .all()
        )
