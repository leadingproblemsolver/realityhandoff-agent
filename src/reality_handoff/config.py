from __future__ import annotations
from urllib.parse import urlparse
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    datahub_mcp_url: str = ""
    datahub_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    allow_datahub_mutations: bool = False
    require_human_approval: bool = True
    demo_target_urn: str = ""
    max_context_entities: int = Field(default=3, ge=1, le=10)
    max_context_rounds: int = Field(default=2, ge=1, le=4)

    @field_validator("datahub_mcp_url")
    @classmethod
    def safe_mcp_url(cls, value: str) -> str:
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("DATAHUB_MCP_URL must be an http(s) URL")
        if parsed.username or parsed.password:
            raise ValueError("Credentials must not be embedded in DATAHUB_MCP_URL")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Plain HTTP is allowed only for a local self-hosted MCP server")
        return value

settings = Settings()
