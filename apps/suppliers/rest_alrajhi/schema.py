from pydantic import BaseModel, Field


class RFQRequest(BaseModel):
    order_id: str
    material_code: str
    quantity: float = Field(gt=0)
    unit: str
    region: str


class RFQResponse(BaseModel):
    quote_id: str
    supplier_id: str
    unit_price: float
    total: float
    lead_time_days: int
    terms: str
