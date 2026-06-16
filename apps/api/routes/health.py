from fastapi import APIRouter

from packages.llm.config import get_llm_settings

router = APIRouter()


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    return {"status": "ready", "llm_mode": get_llm_settings().llm_mode}
