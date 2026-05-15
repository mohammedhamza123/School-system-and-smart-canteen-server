from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class InvoiceCreate(BaseModel):
    student_code: str
    items: list[InvoiceItemCreate]


class InvoiceItemRead(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_total: float

    model_config = {"from_attributes": True}


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    student_id: int
    cashier_id: int
    total_amount: float
    status: str
    created_at: datetime
    items: list[InvoiceItemRead]

    model_config = {"from_attributes": True}
