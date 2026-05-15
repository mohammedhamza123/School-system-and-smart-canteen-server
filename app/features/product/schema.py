from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str
    category: str = "عام"
    sku: str
    price: float = Field(gt=0)
    stock_qty: int = Field(ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock_qty: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductRead(ProductBase):
    id: int

    model_config = {"from_attributes": True}
