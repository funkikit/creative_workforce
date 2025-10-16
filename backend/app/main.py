from fastapi import FastAPI

from .api import router as api_router


def create_application() -> FastAPI:
    app = FastAPI(title="Creative Workforce API")
    app.include_router(api_router)
    return app


app = create_application()
