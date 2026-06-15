from fastapi import APIRouter

from packages.core.models.order import OrderIdentity, ProcurementOrder, RequestPayload

router = APIRouter()


@router.post("")
async def create_order(raw_input: str) -> ProcurementOrder:
    return ProcurementOrder(identity=OrderIdentity(), request=RequestPayload(raw_input=raw_input))
