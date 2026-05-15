from datetime import datetime
from uuid import uuid4


def generate_invoice_number() -> str:
    return f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
