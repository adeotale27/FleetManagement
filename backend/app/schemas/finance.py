from pydantic import BaseModel, Field


class LoginBody(BaseModel):
    email: str
    password: str


class CollectionBody(BaseModel):
    party_id: str
    amount: float = Field(gt=0)
    payment_mode: str = "Cash"
    remarks: str | None = None
    deewanji_id: str | None = None
    against_lr_id: str | None = None
    idempotency_key: str | None = None
