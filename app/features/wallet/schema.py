from pydantic import BaseModel, Field


class WalletRead(BaseModel):
    student_id: int
    balance: float

    model_config = {"from_attributes": True}


class WalletRechargeRequest(BaseModel):
    amount: float = Field(gt=0)
    note: str | None = None
