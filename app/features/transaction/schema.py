from datetime import datetime

from pydantic import BaseModel


class TransactionRead(BaseModel):
    id: int
    student_id: int
    transaction_type: str
    amount: float
    balance_before: float
    balance_after: float
    invoice_id: int | None
    note: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
