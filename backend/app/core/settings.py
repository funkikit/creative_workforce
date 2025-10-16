from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env_target: Literal["local", "gcp"] = "local"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    local_storage_root: str = "data/artifacts"
    database_url: str = "sqlite:///./data/poc.db"
    sqlalchemy_echo: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
