from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.common.enums import InvoiceStatus, TransactionType
from app.core.firebase_push import FirebasePushService
from app.features.invoice.model import Invoice, InvoiceItem
from app.features.notification.model import Notification
from app.features.invoice.repository import InvoiceRepository
from app.features.invoice.schema import InvoiceCreate
from app.features.invoice.utils import generate_invoice_number
from app.features.product.model import Product
from app.features.student.repository import StudentRepository
from app.features.transaction.model import Transaction
from app.features.transaction.repository import TransactionRepository
from app.features.wallet.model import Wallet
from app.features.wallet.repository import WalletRepository


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.student_repo = StudentRepository(db)
        self.wallet_repo = WalletRepository(db)
        self.tx_repo = TransactionRepository(db)

    def create(self, payload: InvoiceCreate, cashier_id: int) -> Invoice:
        student = self.student_repo.get_by_code(payload.student_code)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        wallet = self.wallet_repo.get_by_student_id(student.id)
        if wallet is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

        line_items: list[InvoiceItem] = []
        total_amount = 0.0
        for item in payload.items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product is None or not product.is_active:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")
            if product.stock_qty < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}",
                )
            line_total = product.price * item.quantity
            total_amount += line_total
            line_items.append(
                InvoiceItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=product.price,
                    line_total=line_total,
                )
            )

        balance_before = wallet.balance
        balance_after = balance_before - total_amount
        daily_limit = wallet.daily_spending_limit
        today_spent = self.tx_repo.sum_today_purchases(student.id)

        if daily_limit is not None and daily_limit > 0 and (today_spent + total_amount) > daily_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Daily spending limit exceeded",
            )

        update_result = self.db.execute(
            update(Wallet)
            .where(Wallet.student_id == student.id, Wallet.balance >= total_amount)
            .values(balance=Wallet.balance - total_amount)
        )
        if update_result.rowcount == 0:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient wallet balance")

        for item in line_items:
            self.db.execute(
                update(Product).where(Product.id == item.product_id).values(stock_qty=Product.stock_qty - item.quantity)
            )

        invoice = Invoice(
            invoice_number=generate_invoice_number(),
            student_id=student.id,
            cashier_id=cashier_id,
            total_amount=total_amount,
            status=InvoiceStatus.PAID.value,
        )
        self.invoice_repo.create_invoice(invoice, line_items)

        self.tx_repo.create(
            Transaction(
                student_id=student.id,
                transaction_type=TransactionType.PURCHASE.value,
                amount=total_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                created_by=cashier_id,
                invoice_id=invoice.id,
                note="POS purchase",
            )
        )
        self.db.add(
            Notification(
                student_id=student.id,
                title="عملية شراء جديدة",
                body=(
                    f"قام الطالب {student.full_name} بعملية شراء من المقصف بقيمة "
                    f"{total_amount:.2f}. الرصيد المتبقي {balance_after:.2f}."
                ),
                is_important=True,
                created_by=cashier_id,
            )
        )
        self.db.commit()
        invoice.items = line_items
        FirebasePushService(self.db).send_to_parent(
            student_id=student.id,
            title="عملية شراء جديدة",
            body=(
                f"قام الطالب {student.full_name} بعملية شراء من المقصف بقيمة "
                f"{total_amount:.2f}. الرصيد المتبقي {balance_after:.2f}."
            ),
            data={
                "type": "purchase",
                "screen": "transactions",
                "student_id": student.id,
            },
        )
        return invoice

    def list_all(self) -> list[Invoice]:
        invoices = self.invoice_repo.list_all()
        for invoice in invoices:
            invoice.items = self.invoice_repo.get_items(invoice.id)
        return invoices
