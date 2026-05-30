from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProviderPayload(BaseModel):
    provider: str
    displayName: str
    baseUrl: str | None = None
    apiKey: str | None = None
    defaultModel: str | None = None
    timeoutSeconds: int = 60
    maxRetries: int = 2
    enabled: bool = True
    priority: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderRemovePayload(BaseModel):
    slug: str


class SecretPayload(BaseModel):
    provider: str
    apiKey: str
    envVar: str | None = None


class EndpointPayload(BaseModel):
    name: str
    path: str
    method: Literal["POST", "GET"] = "POST"
    category: str = "custom"
    summary: str = ""
    endpointType: Literal["chat", "completion", "embedding", "image", "audio"] = "chat"
    compatibilities: list[str] = Field(default_factory=lambda: ["openai"])
    modelName: str | None = None
    blocks: dict[str, Any] = Field(default_factory=dict)
    providerOrder: list[str] = Field(default_factory=list)
    authMode: Literal["public", "dashboard_password"] = "public"
    cacheEnabled: bool = False
    cacheMode: Literal["memory", "sqlite"] = "memory"
    cacheTtlSeconds: int = 300
    rateLimitPerMinute: int = 60


class EndpointDeletePayload(BaseModel):
    id: int


class EndpointClonePayload(BaseModel):
    id: int
    name: str | None = None
    path: str | None = None


class TestGatewayPayload(BaseModel):
    endpointType: Literal["chat", "completion", "embedding", "image", "audio"] = "chat"
    compatibilities: list[str] = Field(default_factory=lambda: ["openai"])
    providerOrder: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    cacheEnabled: bool = False
    cacheMode: Literal["memory", "sqlite"] = "memory"
    cacheTtlSeconds: int = 300
    requestPath: str = "/api/gateway/test"


class LoginPayload(BaseModel):
    password: str


class SettingsPayload(BaseModel):
    dashboardAuthEnabled: bool = False
    password: str | None = None
    corsOrigins: list[str] = Field(default_factory=lambda: ["*"])
    defaultTimeoutSeconds: int = 60
    defaultRateLimitPerMinute: int = 120
    endpointStyle: Literal["openai", "anthropic", "gemini", "lm-studio"] = "openai"
    csrfEnabled: bool = True
    secureHeadersEnabled: bool = True


class DeploymentPayload(BaseModel):
    target: Literal[
        "windows-exe",
        "linux-binary",
        "macos-app",
        "docker",
        "render",
        "railway",
        "flyio",
        "vps",
        "vercel",
        "cloudflare-workers",
        "netlify",
    ]
    flowPath: str | None = None
    endpointStyle: Literal["openai", "anthropic", "gemini", "lm-studio"] = "openai"
    dashboardAuthEnabled: bool = False
    password: str | None = None
    notes: str | None = None
    autoBuild: bool = False
    outputDir: str | None = None


class DocsResponse(BaseModel):
    sections: list[dict[str, Any]]
