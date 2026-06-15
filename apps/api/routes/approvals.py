from fastapi import APIRouter

router = APIRouter()


@router.post("/{order_id}/approve")
async def approve_order(order_id: str) -> dict[str, str]:
    return {"order_id": order_id, "status": "approved"}


@router.post("/{order_id}/reject")
async def reject_order(order_id: str) -> dict[str, str]:
    return {"order_id": order_id, "status": "rejected"}
