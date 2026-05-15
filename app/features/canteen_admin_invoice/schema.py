from datetime import datetime

from pydantic import BaseModel, Field


class CanteenAdminInvoiceItemCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    quantity: int = Field(gt=0)
    wholesale_price: float = Field(gt=0)
    sale_price: float = Field(gt=0)
    barcode: str | None = Field(default=None, max_length=120)


class CanteenAdminInvoiceCreate(BaseModel):
    items: list[CanteenAdminInvoiceItemCreate] = Field(min_length=1)


class CanteenAdminInvoiceItemRead(BaseModel):
    id: int
    product_name: str
    category: str
    quantity: int
    wholesale_price: float
    sale_price: float
    line_wholesale_total: float
    line_sale_total: float
    line_profit: float
    barcode: str
    is_system_barcode: bool

    model_config = {"from_attributes": True}


class CanteenAdminInvoiceRead(BaseModel):
    id: int
    invoice_number: str
    category: str
    total_wholesale: float
    total_sale: float
    expected_profit: float
    status: str
    created_by: int
    created_at: datetime
    items: list[CanteenAdminInvoiceItemRead]

    model_config = {"from_attributes": True}
