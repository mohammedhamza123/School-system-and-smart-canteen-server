from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CanteenAdminInvoice(Base):
    __tablename__ = "canteen_admin_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    total_wholesale: Mapped[float] = mapped_column(Float, default=0)
    total_sale: Mapped[float] = mapped_column(Float, default=0)
    expected_profit: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default="posted")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CanteenAdminInvoiceItem(Base):
    __tablename__ = "canteen_admin_invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("canteen_admin_invoices.id"), index=True)
    product_name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    wholesale_price: Mapped[float] = mapped_column(Float)
    sale_price: Mapped[float] = mapped_column(Float)
    line_wholesale_total: Mapped[float] = mapped_column(Float)
    line_sale_total: Mapped[float] = mapped_column(Float)
    line_profit: Mapped[float] = mapped_column(Float)
    barcode: Mapped[str] = mapped_column(String(120), index=True)
    is_system_barcode: Mapped[bool] = mapped_column(Boolean, default=False)
