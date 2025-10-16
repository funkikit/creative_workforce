from functools import lru_cache
from typing import Literal

from pydantic import BaseSettings


class Settings(BaseSettings):
    env_target: Literal["local", "gcp"] = "local"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
