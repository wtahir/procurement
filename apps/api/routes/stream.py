from fastapi import APIRouter

router = APIRouter()


@router.get("/orders/{order_id}")
async def stream_placeholder(order_id: str) -> dict[str, str]:
    return {"order_id": order_id, "status": "stream-not-wired"}
