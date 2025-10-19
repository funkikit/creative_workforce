from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    env_target: Literal["local", "gcp"] = "local"
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    llm_provider: Literal["local", "openai"] = "local"
    llm_model: str = "gpt-4o-mini"
    llm_output_style: str = "クリエイティブ・ブリーフ"
    image_provider: Literal["placeholder", "gemini"] = "placeholder"
    image_model: str = "imagen-3.0-generate"
    local_storage_root: str = "data/artifacts"
    database_url: str = "sqlite:///./data/poc.db"
    sqlalchemy_echo: bool = False
    gcp_project: str | None = None
    gcp_location: str = "asia-northeast1"
    gcs_bucket: str | None = None
    gcs_base_path: str = "artifacts"
    cloud_tasks_project: str | None = None
    cloud_tasks_location: str | None = None
    cloud_tasks_queue_id: str | None = None
    cloud_tasks_target_url: str | None = None
    cloud_tasks_service_account_email: str | None = None
    vertex_project: str | None = None
    vertex_location: str | None = None
    vertex_embedding_model: str = "textembedding-gecko@003"
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    @field_validator("cors_allow_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
