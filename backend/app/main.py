from fastapi import FastAPI

from .api.router import router as api_router
from .core.db import init_db


def create_application() -> FastAPI:
    app = FastAPI(title="Creative Workforce API")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(api_router)
    return app


app = create_application()
