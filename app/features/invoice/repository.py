from sqlalchemy.orm import Session

from app.features.invoice.model import Invoice, InvoiceItem


class InvoiceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_invoice(self, invoice: Invoice, items: list[InvoiceItem]) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        for item in items:
            item.invoice_id = invoice.id
            self.db.add(item)
        self.db.flush()
        return invoice

    def list_all(self) -> list[Invoice]:
        return self.db.query(Invoice).order_by(Invoice.id.desc()).all()

    def get_items(self, invoice_id: int) -> list[InvoiceItem]:
        return self.db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).all()
