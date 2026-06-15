from fastapi import APIRouter
from pydantic import BaseModel, Field

from apps.api.errors import ProcuraError
from apps.api.store import get_order, list_orders, save_order
from packages.agents.pipeline import order_summary, run_demo_pipeline
from packages.core.models.order import ProcurementOrder

router = APIRouter()


class CreateOrderRequest(BaseModel):
    raw_input: str = Field(min_length=1)
    material_code: str = "rebar_steel"
    quantity: float = Field(default=500, gt=0)
    region: str = "riyadh"


@router.post("")
async def create_order(payload: CreateOrderRequest) -> ProcurementOrder:
    order = run_demo_pipeline(
        raw_input=payload.raw_input,
        material_code=payload.material_code,
        quantity=payload.quantity,
        region=payload.region,
    )
    return save_order(order)


@router.get("")
async def list_all_orders() -> list[dict[str, object]]:
    return [order_summary(order) for order in list_orders()]


@router.get("/{order_id}")
async def get_single_order(order_id: str) -> ProcurementOrder:
    order = get_order(order_id)
    if order is None:
        raise ProcuraError(f"Order {order_id} not found", status_code=404)
    return order
