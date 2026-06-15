from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_voice_request() -> dict[str, str]:
    return {"status": "voice-not-implemented"}
