from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_storage_service,
    get_task_queue_service,
    get_vector_store_service,
)
from app.services.base import StorageService, TaskQueueService, VectorStoreService

from .projects import router as projects_router


router = APIRouter(prefix="/api")
router.include_router(projects_router)


@router.get("/health", tags=["system"])
async def healthcheck(
    _: StorageService = Depends(get_storage_service),
    __: TaskQueueService = Depends(get_task_queue_service),
    ___: VectorStoreService = Depends(get_vector_store_service),
) -> dict:
    return {"status": "ok"}
