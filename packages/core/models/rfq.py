from datetime import date

from pydantic import BaseModel, Field


class StandardRFQ(BaseModel):
    order_id: str
    material_code: str
    quantity: float = Field(gt=0)
    unit: str
    region: str
    needed_by: date | None = None
