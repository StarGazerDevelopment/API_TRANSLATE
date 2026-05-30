from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Provider(Base, TimestampMixin):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    env_var: Mapped[str] = mapped_column(String(255), unique=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transport: Mapped[str] = mapped_column(String(100), default="openai_compatible")
    default_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    max_retries: Mapped[int] = mapped_column(Integer, default=2)
    health_status: Mapped[str] = mapped_column(String(50), default="unknown")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class Endpoint(Base, TimestampMixin):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    method: Mapped[str] = mapped_column(String(20), default="POST")
    category: Mapped[str] = mapped_column(String(50), default="custom")
    summary: Mapped[str] = mapped_column(Text, default="")
    endpoint_type: Mapped[str] = mapped_column(String(50), default="chat")
    compatibility_json: Mapped[str] = mapped_column(Text, default='["openai"]')
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blockly_json: Mapped[str] = mapped_column(Text, default="{}")
    generated_code: Mapped[str] = mapped_column(Text, default="")
    provider_order_json: Mapped[str] = mapped_column(Text, default="[]")
    auth_mode: Mapped[str] = mapped_column(String(50), default="public")
    cache_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    cache_mode: Mapped[str] = mapped_column(String(50), default="memory")
    cache_ttl_seconds: Mapped[int] = mapped_column(Integer, default=300)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint_path: Mapped[str] = mapped_column(String(255), index=True)
    provider_slug: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    failover_used: Mapped[bool] = mapped_column(Boolean, default=False)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    request_excerpt: Mapped[str] = mapped_column(Text, default="")
    response_excerpt: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CacheEntry(Base):
    __tablename__ = "cache_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    storage_mode: Mapped[str] = mapped_column(String(50), default="sqlite")
    payload_json: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dashboard_auth_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_secret: Mapped[str] = mapped_column(String(255))
    cors_origins_json: Mapped[str] = mapped_column(Text, default='["*"]')
    default_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60)
    default_rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=120)
    endpoint_style: Mapped[str] = mapped_column(String(50), default="openai")
    csrf_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    secure_headers_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeploymentTarget(Base):
    __tablename__ = "deployment_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(100))
    output_path: Mapped[str] = mapped_column(String(500))
    manifest_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
