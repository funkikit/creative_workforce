import asyncio

from httpx import AsyncClient

from app.main import app


async def test_healthcheck() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


if __name__ == "__main__":
    asyncio.run(test_healthcheck())
