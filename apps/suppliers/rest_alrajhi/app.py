from uuid import uuid4

from fastapi import APIRouter

from apps.suppliers.common.pricing import quote_price
from apps.suppliers.rest_alrajhi.schema import RFQRequest, RFQResponse

router = APIRouter()


@router.get("/catalog")
async def get_catalog() -> dict[str, object]:
    return {
        "supplier_id": "al_rajhi_steel",
        "materials": ["rebar_steel", "cement_bag"],
        "regions": ["riyadh", "jeddah", "dammam"],
    }


@router.post("/rfq", response_model=RFQResponse)
async def create_rfq(payload: RFQRequest) -> RFQResponse:
    unit_price = quote_price(payload.material_code, payload.region, payload.quantity, markup=1.01)
    total = round(unit_price * payload.quantity, 2)
    return RFQResponse(
        quote_id=str(uuid4()),
        supplier_id="al_rajhi_steel",
        unit_price=unit_price,
        total=total,
        lead_time_days=2,
        terms="30% upfront, balance on delivery",
    )
