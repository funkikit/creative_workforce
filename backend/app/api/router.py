from fastapi import APIRouter


router = APIRouter(prefix="/api")


@router.get("/health", tags=["system"])
async def healthcheck() -> dict:
    return {"status": "ok"}
