from pydantic import BaseModel, Field

from packages.core.enums import SupplierChannel


class SupplierDescriptor(BaseModel):
    supplier_id: str
    name: str
    channel: SupplierChannel
    materials: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    min_order: float = Field(ge=0)
    reliability_score: float = Field(default=1.0, ge=0, le=1)
