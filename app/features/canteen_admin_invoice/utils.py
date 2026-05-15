import secrets
from datetime import datetime


def generate_canteen_admin_invoice_number() -> str:
    now = datetime.utcnow()
    date_part = now.strftime("%Y%m%d")
    token_part = secrets.token_hex(2).upper()
    return f"CM-{date_part}-{token_part}"


def generate_system_barcode() -> str:
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    random_part = secrets.token_hex(3).upper()
    return f"SYS-{timestamp}-{random_part}"
