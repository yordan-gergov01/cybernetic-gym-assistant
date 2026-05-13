from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Fitness AI API"

    APP_ENV: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_URL: str

    OPENAI_API_KEY: str
    GEMINI_API_KEY: str = ""

    USDA_API_KEY: str = "DEMO_KEY"
    USDA_BASE_URL: str = "https://api.nal.usda.gov/fdc/v1"

    PRIMARY_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    GEMINI_VISION_MODEL: str = "gemini-2.5-flash"

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 100
    RETRIEVAL_TOP_K: int = 8
    RERANKING_TOP_N: int = 4

    RESPONSE_LANGUAGE: str = "bulgarian"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated origins for FastAPI CORSMiddleware",
    )

    VECTORSTORE_DIR: str = "data/vectorstore"
    FAISS_INDEX_FILE: str = "henselmans_openai.index"
    FAISS_METADATA_FILE: str = "henselmans_openai_metadata.json"

    @property
    def backend_root(self) -> Path:
        return _BACKEND_ROOT

    @property
    def vectorstore_path(self) -> Path:
        p = Path(self.VECTORSTORE_DIR)
        if not p.is_absolute():
            p = _BACKEND_ROOT / p
        return p.resolve()

    @property
    def faiss_index_path(self) -> Path:
        return self.vectorstore_path / self.FAISS_INDEX_FILE

    @property
    def faiss_metadata_path(self) -> Path:
        return self.vectorstore_path / self.FAISS_METADATA_FILE

    @property
    def cors_origins_list(self) -> list[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
