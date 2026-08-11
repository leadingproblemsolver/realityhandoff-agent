from __future__ import annotations

from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Canonical self-hosted DataHub Core path.
    datahub_gms_url: str = "http://localhost:8080"
    datahub_gms_token: str = ""
    datahub_server_mutations_enabled: bool = False
    save_document_tool_enabled: bool = True

    # Optional managed / remote MCP path. If both are set, it takes precedence over stdio.
    datahub_mcp_url: str = ""
    datahub_token: str = ""

    # BYOK semantic compiler. Deterministic Python retains authorization authority.
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # Agent-side safety boundary. This is deliberately separate from MCP-server tool exposure.
    allow_datahub_mutations: bool = False
    require_human_approval: bool = True
    demo_target_urn: str = ""
    max_context_entities: int = Field(default=3, ge=1, le=10)
    max_context_rounds: int = Field(default=2, ge=1, le=4)

    @field_validator("datahub_mcp_url", "datahub_gms_url")
    @classmethod
    def safe_url(cls, value: str) -> str:
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("DataHub URL must be an http(s) URL")
        if parsed.username or parsed.password:
            raise ValueError("Credentials must not be embedded in DataHub URLs")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Plain HTTP is allowed only for local DataHub endpoints")
        return value.rstrip("/")


settings = Settings()
