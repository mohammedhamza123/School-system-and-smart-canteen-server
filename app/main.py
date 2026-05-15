from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.common.enums import UserRole
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.logger import configure_logging
from app.core.security import get_password_hash
from app.features.auth.router import router as auth_router
from app.features.canteen_admin_invoice import model as canteen_admin_invoice_models
from app.features.canteen_admin_invoice.router import router as canteen_admin_invoice_router
from app.features.canteen_admin_invoice.service import backfill_missing_products_from_admin_invoices
from app.features.invoice import model as invoice_models
from app.features.invoice.router import router as invoice_router
from app.features.notification import model as notification_models
from app.features.notification.router import router as notification_router
from app.features.parent_portal.router import router as parent_portal_router
from app.features.product import model as product_models
from app.features.product.router import router as product_router
from app.features.student import model as student_models
from app.features.student.router import router as student_router
from app.features.transaction import model as transaction_models
from app.features.transaction.router import router as transaction_router
from app.features.user.model import User
from app.features.user.router import router as user_router
from app.features.user.service import DEFAULT_ADMIN_SETTINGS
from app.features.wallet import model as wallet_models
from app.features.wallet.router import router as wallet_router

configure_logging()

# Keep model imports referenced so table metadata is registered.
_registered_models = (
    student_models,
    wallet_models,
    transaction_models,
    product_models,
    invoice_models,
    canteen_admin_invoice_models,
    notification_models,
)

app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_student_table_columns()
    _ensure_user_table_columns()
    _ensure_product_table_columns()
    _ensure_wallet_table_columns()
    db = SessionLocal()
    try:
        # Ensure there is always one platform owner account.
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None:
            db.add(
                User(
                    username="admin",
                    full_name="System Admin",
                    password_hash=get_password_hash("Admin@123"),
                    role=UserRole.ADMIN.value,
                    settings=DEFAULT_ADMIN_SETTINGS.copy(),
                )
            )
            db.commit()
        elif admin.role == UserRole.ADMIN.value and not isinstance(admin.settings, dict):
            admin.settings = DEFAULT_ADMIN_SETTINGS.copy()
            db.commit()
        elif admin.role == UserRole.ADMIN.value:
            merged_settings = DEFAULT_ADMIN_SETTINGS.copy()
            merged_settings.update(admin.settings)
            admin.settings = merged_settings
            db.commit()

        # Legacy canteen-admin invoices should populate the POS products catalog.
        backfill_missing_products_from_admin_invoices(db)
    finally:
        db.close()


def _ensure_student_table_columns() -> None:
    inspector = inspect(engine)
    if "students" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("students")}
    pending_columns = [
        ("national_id", "VARCHAR(30)"),
        ("photo_url", "VARCHAR(500)"),
        ("blood_type", "VARCHAR(10)"),
        ("has_chronic_disease", "BOOLEAN NOT NULL DEFAULT 0"),
        ("chronic_disease_details", "VARCHAR(300)"),
        ("card_issued_at", "DATETIME"),
        ("card_issued_by", "VARCHAR(150)"),
        ("card_issue_count", "INTEGER NOT NULL DEFAULT 0"),
    ]

    with engine.begin() as connection:
        for column_name, column_type in pending_columns:
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE students ADD COLUMN {column_name} {column_type}")
                )

        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_students_national_id "
                "ON students (national_id)"
            )
        )


def _ensure_user_table_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "settings" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN settings TEXT NOT NULL DEFAULT '{}'"))


def _ensure_product_table_columns() -> None:
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("products")}
    if "category" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE products ADD COLUMN category VARCHAR(60) NOT NULL DEFAULT 'عام'")
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_products_category "
                "ON products (category)"
            )
        )


def _ensure_wallet_table_columns() -> None:
    inspector = inspect(engine)
    if "wallets" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("wallets")}
    if "daily_spending_limit" in existing_columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE wallets ADD COLUMN daily_spending_limit FLOAT")
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(user_router, prefix=api_prefix)
app.include_router(student_router, prefix=api_prefix)
app.include_router(wallet_router, prefix=api_prefix)
app.include_router(transaction_router, prefix=api_prefix)
app.include_router(product_router, prefix=api_prefix)
app.include_router(invoice_router, prefix=api_prefix)
app.include_router(canteen_admin_invoice_router, prefix=api_prefix)
app.include_router(notification_router, prefix=api_prefix)
app.include_router(parent_portal_router, prefix=api_prefix)
