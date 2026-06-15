from fastapi import APIRouter

router = APIRouter()


@router.post("/supplier/edi")
async def receive_supplier_event(payload: dict[str, object]) -> dict[str, object]:
    return {"accepted": True, "payload": payload}
