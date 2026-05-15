from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STUDENT_MANAGER = "student_manager"
    CARD_ISSUER = "card_issuer"
    FINANCE = "finance"
    PARENT = "parent"
    CANTEEN_STAFF = "canteen_staff"


class TransactionType(str, Enum):
    RECHARGE = "recharge"
    PURCHASE = "purchase"


class InvoiceStatus(str, Enum):
    PAID = "paid"
    CANCELLED = "cancelled"
