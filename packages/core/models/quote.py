from pydantic import BaseModel, Field


class StandardQuote(BaseModel):
    supplier_id: str
    unit_price: float = Field(gt=0)
    total: float = Field(gt=0)
    lead_time_days: int = Field(ge=0)
    terms: str
    raw_ref: str


class QuotePending(BaseModel):
    supplier_id: str
    handle_id: str
    message: str = "Quote not ready yet"


class QuoteError(BaseModel):
    supplier_id: str
    code: str
    message: str
    retryable: bool = True
