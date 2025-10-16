from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.router import router as api_router
from .core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_application() -> FastAPI:
    app = FastAPI(title="Creative Workforce API", lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_application()
