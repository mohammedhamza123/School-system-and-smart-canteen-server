from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.features.canteen_admin_invoice.model import CanteenAdminInvoice, CanteenAdminInvoiceItem
from app.features.canteen_admin_invoice.repository import CanteenAdminInvoiceRepository
from app.features.canteen_admin_invoice.schema import CanteenAdminInvoiceCreate
from app.features.product.model import Product
from app.features.canteen_admin_invoice.utils import (
    generate_canteen_admin_invoice_number,
    generate_system_barcode,
)


def sync_posted_items_to_products(db: Session, items: list[CanteenAdminInvoiceItem]) -> None:
    for item in items:
        sku = item.barcode.strip()
        if not sku:
            continue

        product = db.query(Product).filter(Product.sku == sku).first()
        if product is None:
            db.add(
                Product(
                    name=item.product_name,
                    category=item.category,
                    sku=sku,
                    price=item.sale_price,
                    stock_qty=item.quantity,
                    is_active=True,
                )
            )
            continue

        product.name = item.product_name
        product.category = item.category
        product.price = item.sale_price
        product.stock_qty += item.quantity
        product.is_active = True


def backfill_missing_products_from_admin_invoices(db: Session) -> int:
    created_count = 0
    aggregated_items: dict[str, dict[str, str | float | int]] = {}
    invoice_items = db.query(CanteenAdminInvoiceItem).all()

    for item in invoice_items:
        sku = item.barcode.strip()
        if not sku or db.query(Product).filter(Product.sku == sku).first() is not None:
            continue

        if sku not in aggregated_items:
            aggregated_items[sku] = {
                "name": item.product_name,
                "category": item.category,
                "price": item.sale_price,
                "stock_qty": item.quantity,
            }
            continue

        aggregated_items[sku]["stock_qty"] = int(aggregated_items[sku]["stock_qty"]) + item.quantity
        aggregated_items[sku]["price"] = item.sale_price
        aggregated_items[sku]["name"] = item.product_name
        aggregated_items[sku]["category"] = item.category

    for sku, data in aggregated_items.items():
        db.add(
            Product(
                name=str(data["name"]),
                category=str(data["category"]),
                sku=sku,
                price=float(data["price"]),
                stock_qty=int(data["stock_qty"]),
                is_active=True,
            )
        )
        created_count += 1

    if created_count:
        db.commit()

    return created_count


class CanteenAdminInvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CanteenAdminInvoiceRepository(db)

    def create_posted(self, payload: CanteenAdminInvoiceCreate, created_by: int) -> CanteenAdminInvoice:
        items: list[CanteenAdminInvoiceItem] = []
        categories: set[str] = set()
        total_wholesale = 0.0
        total_sale = 0.0

        for item in payload.items:
            product_name = item.product_name.strip()
            category_name = item.category.strip()
            if not product_name or not category_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product name and category are required",
                )
            if item.sale_price < item.wholesale_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sale price cannot be lower than wholesale for {product_name}",
                )

            line_wholesale_total = item.wholesale_price * item.quantity
            line_sale_total = item.sale_price * item.quantity
            line_profit = line_sale_total - line_wholesale_total
            categories.add(category_name)
            total_wholesale += line_wholesale_total
            total_sale += line_sale_total

            barcode_value = item.barcode.strip() if item.barcode else ""
            is_system_barcode = not barcode_value
            if is_system_barcode:
                barcode_value = generate_system_barcode()

            items.append(
                CanteenAdminInvoiceItem(
                    product_name=item.product_name.strip(),
                    category=category_name,
                    quantity=item.quantity,
                    wholesale_price=item.wholesale_price,
                    sale_price=item.sale_price,
                    line_wholesale_total=line_wholesale_total,
                    line_sale_total=line_sale_total,
                    line_profit=line_profit,
                    barcode=barcode_value,
                    is_system_barcode=is_system_barcode,
                )
            )

        invoice_category = categories.pop() if len(categories) == 1 else "مختلطة"
        invoice = CanteenAdminInvoice(
            invoice_number=generate_canteen_admin_invoice_number(),
            category=invoice_category,
            total_wholesale=total_wholesale,
            total_sale=total_sale,
            expected_profit=total_sale - total_wholesale,
            status="posted",
            created_by=created_by,
        )
        self.repo.create_invoice(invoice, items)
        sync_posted_items_to_products(self.db, items)
        self.db.commit()

        invoice.items = items
        return invoice

    def list_all(self, category: str | None = None) -> list[CanteenAdminInvoice]:
        invoices = self.repo.list_by_category(category) if category else self.repo.list_all()
        for invoice in invoices:
            invoice.items = self.repo.get_items(invoice.id)
        return invoices
