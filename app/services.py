from __future__ import annotations

import hashlib
import json
import os
import platform
import secrets
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import ENV_FILE, EXPORTS_DIR, ROOT_DIR, settings
from app.models import AuthSession, CacheEntry, DeploymentTarget, Endpoint, Provider, RequestLog, Setting
from app.providers import PROVIDER_CATALOG, ProviderInvoker, ProviderRuntimeConfig, catalog_lookup


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    visible = min(4, len(value))
    return f"{value[:visible]}{'*' * max(8, len(value) - visible)}"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def ensure_default_state(db: Session) -> None:
    if not db.scalar(select(Setting.id).limit(1)):
        db.add(
            Setting(
                dashboard_auth_enabled=False,
                session_secret=secrets.token_urlsafe(32),
                cors_origins_json='["*"]',
                default_timeout_seconds=60,
                default_rate_limit_per_minute=120,
                endpoint_style="openai",
                csrf_enabled=True,
                secure_headers_enabled=True,
            )
        )
        db.commit()

    if not db.scalar(select(Endpoint.id).where(Endpoint.path == "/api/translate").limit(1)):
        sample_blocks = {
            "version": 1,
            "blocks": [
                {"id": "on-api-call", "type": "on_api_call", "config": {"path": "/api/translate", "method": "POST"}},
                {"id": "call-api", "type": "call_api", "config": {"provider": "openai", "model": "gpt-4o-mini"}},
            ],
        }
        db.add(
            Endpoint(
                name="Translate",
                path="/api/translate",
                method="POST",
                category="translation",
                summary="Default translation workflow that starts on API call and forwards to the selected provider.",
                endpoint_type="chat",
                compatibility_json=json.dumps(["openai", "anthropic", "gemini"]),
                model_name="gpt-4o-mini",
                blockly_json=json.dumps(sample_blocks),
                generated_code=generate_endpoint_preview("/api/translate", "POST", sample_blocks, "chat", ["openai", "anthropic", "gemini"], "gpt-4o-mini"),
                provider_order_json=json.dumps(["openai", "groq", "openrouter", "google_gemini"]),
                auth_mode="public",
                cache_enabled=True,
                cache_mode="sqlite",
                cache_ttl_seconds=600,
            )
        )
        db.commit()


def generate_endpoint_preview(
    path: str,
    method: str,
    blocks: dict[str, Any],
    endpoint_type: str = "chat",
    compatibilities: list[str] | None = None,
    model_name: str | None = None,
) -> str:
    compatibilities = compatibilities or ["openai"]
    workspace = blocks.get("blocks", {}) if isinstance(blocks, dict) else {}
    block_items = workspace.get("blocks", []) if isinstance(workspace, dict) else []
    default_lines = [
        "on_api_call()",
        "call_api(provider='openai', model='gpt-4o-mini')",
    ]
    block_lines: list[str] = []
    for block in block_items:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", "step"))
        config = block.get("config", {})
        fields = block.get("fields", {}) if isinstance(block.get("fields"), dict) else {}
        if block_type == "on_api_call":
            route_path = fields.get("PATH") or config.get("path", path)
            route_method = fields.get("METHOD") or config.get("method", method)
            block_lines.append(f"on_api_call(path='{route_path}', method='{route_method}')")
        elif block_type == "call_api":
            provider = fields.get("PROVIDER") or config.get("provider", "primary")
            model = fields.get("MODEL") or config.get("model") or model_name or "auto"
            block_lines.append(f"call_api(provider='{provider}', model='{model}')")
        elif block_type == "repeat_times":
            count = fields.get("COUNT") or config.get("count", 3)
            block_lines.append(f"repeat_times(count={count})")
        elif block_type == "repeat_until_true":
            condition = fields.get("CONDITION") or "response.ok"
            block_lines.append(f"repeat_until_true(condition='{condition}')")
        elif block_type == "custom_code":
            code = fields.get("CODE") or "..."
            block_lines.append(f"custom_code('{code}')")
        else:
            block_lines.append(f"{block_type}({json.dumps(config, default=str)})")

    rendered_lines = block_lines or default_lines
    header = [
        f"# API Builder workflow for {path}",
        f"# Method: {method}",
        f"# Request type: {endpoint_type}",
        f"# Compatible with: {', '.join(compatibilities)}",
    ]
    return "\n".join(header + [""] + rendered_lines)


def get_env_values() -> dict[str, str]:
    if not ENV_FILE.exists():
        ENV_FILE.write_text("", encoding="utf-8")
    values = dotenv_values(ENV_FILE)
    return {key: value or "" for key, value in values.items()}


def write_env_value(key: str, value: str) -> None:
    current = get_env_values()
    current[key] = value
    lines = [f"{env_key}={env_value}" for env_key, env_value in sorted(current.items())]
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_catalog() -> list[dict[str, str]]:
    return PROVIDER_CATALOG


def serialize_provider(record: Provider) -> dict[str, Any]:
    env_value = get_env_values().get(record.env_var)
    catalog_item = catalog_lookup(record.slug) or {}
    return {
        "id": record.id,
        "slug": record.slug,
        "displayName": record.display_name,
        "envVar": record.env_var,
        "baseUrl": record.base_url,
        "transport": record.transport,
        "defaultModel": record.default_model,
        "enabled": record.enabled,
        "priority": record.priority,
        "timeoutSeconds": record.timeout_seconds,
        "maxRetries": record.max_retries,
        "healthStatus": record.health_status,
        "maskedKey": mask_secret(env_value),
        "metadata": json.loads(record.metadata_json or "{}"),
        "logoText": catalog_item.get("logo_text", record.display_name[:2].upper()),
        "logoColor": catalog_item.get("logo_color", "#475569"),
        "models": catalog_item.get("models", []),
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }


def serialize_endpoint(record: Endpoint) -> dict[str, Any]:
    return {
        "id": record.id,
        "name": record.name,
        "path": record.path,
        "method": record.method,
        "category": record.category,
        "summary": record.summary,
        "endpointType": record.endpoint_type,
        "compatibilities": json.loads(record.compatibility_json or '["openai"]'),
        "modelName": record.model_name,
        "blocks": json.loads(record.blockly_json or "{}"),
        "generatedCode": record.generated_code,
        "providerOrder": json.loads(record.provider_order_json or "[]"),
        "authMode": record.auth_mode,
        "cacheEnabled": record.cache_enabled,
        "cacheMode": record.cache_mode,
        "cacheTtlSeconds": record.cache_ttl_seconds,
        "rateLimitPerMinute": record.rate_limit_per_minute,
        "enabled": record.enabled,
        "updatedAt": record.updated_at.isoformat() if record.updated_at else None,
    }


class MemoryCache:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        item = self._cache.get(key)
        if not item:
            return None
        expires_at, payload = item
        if expires_at <= now_utc():
            self._cache.pop(key, None)
            return None
        return payload

    def set(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        self._cache[key] = (now_utc() + timedelta(seconds=ttl_seconds), payload)


memory_cache = MemoryCache()


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def settings_record(self) -> Setting:
        record = self.db.scalar(select(Setting).limit(1))
        if not record:
            ensure_default_state(self.db)
            record = self.db.scalar(select(Setting).limit(1))
        assert record is not None
        return record

    def login(self, password: str) -> dict[str, str]:
        settings_record = self.settings_record()
        if not settings_record.password_hash or not pwd_context.verify(password, settings_record.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password.")

        raw_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(24)
        self.db.add(
            AuthSession(
                session_token_hash=stable_hash(raw_token),
                expires_at=now_utc() + timedelta(hours=settings.session_ttl_hours),
            )
        )
        self.db.commit()
        return {"session": raw_token, "csrf": csrf_token}

    def logout(self, session_token: str | None) -> None:
        if not session_token:
            return
        record = self.db.scalar(select(AuthSession).where(AuthSession.session_token_hash == stable_hash(session_token)))
        if record:
            self.db.delete(record)
            self.db.commit()

    def is_dashboard_protected(self) -> bool:
        return self.settings_record().dashboard_auth_enabled

    def verify_session(self, session_token: str | None) -> bool:
        if not self.is_dashboard_protected():
            return True
        if not session_token:
            return False
        record = self.db.scalar(select(AuthSession).where(AuthSession.session_token_hash == stable_hash(session_token)))
        if not record:
            return False
        if record.expires_at <= now_utc():
            self.db.delete(record)
            self.db.commit()
            return False
        return True

    def update_settings(self, payload: dict[str, Any]) -> Setting:
        record = self.settings_record()
        record.dashboard_auth_enabled = payload["dashboardAuthEnabled"]
        record.cors_origins_json = json.dumps(payload["corsOrigins"])
        record.default_timeout_seconds = payload["defaultTimeoutSeconds"]
        record.default_rate_limit_per_minute = payload["defaultRateLimitPerMinute"]
        record.endpoint_style = payload["endpointStyle"]
        record.csrf_enabled = payload["csrfEnabled"]
        record.secure_headers_enabled = payload["secureHeadersEnabled"]
        if payload.get("password"):
            record.password_hash = pwd_context.hash(payload["password"])
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record


class GatewayService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.invoker = ProviderInvoker()

    def _load_provider_configs(self, slugs: list[str]) -> list[Provider]:
        providers = self.db.scalars(select(Provider).where(Provider.slug.in_(slugs), Provider.enabled.is_(True))).all()
        ranked = {provider.slug: provider for provider in providers}
        return [ranked[slug] for slug in slugs if slug in ranked]

    def _runtime_config(self, record: Provider) -> ProviderRuntimeConfig | None:
        env_values = get_env_values()
        api_key = env_values.get(record.env_var, "")
        if not api_key:
            return None
        return ProviderRuntimeConfig(
            slug=record.slug,
            display_name=record.display_name,
            env_var=record.env_var,
            api_key=api_key,
            base_url=record.base_url or "",
            transport=record.transport,
            default_model=record.default_model,
            timeout_seconds=record.timeout_seconds,
        )

    def _read_cache(self, cache_key: str, mode: str) -> dict[str, Any] | None:
        if mode == "memory":
            return memory_cache.get(cache_key)
        record = self.db.scalar(select(CacheEntry).where(CacheEntry.cache_key == cache_key))
        if not record or record.expires_at <= now_utc():
            return None
        return json.loads(record.payload_json)

    def _write_cache(self, cache_key: str, mode: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        if mode == "memory":
            memory_cache.set(cache_key, payload, ttl_seconds)
            return
        expires_at = now_utc() + timedelta(seconds=ttl_seconds)
        existing = self.db.scalar(select(CacheEntry).where(CacheEntry.cache_key == cache_key))
        if not existing:
            existing = CacheEntry(cache_key=cache_key, storage_mode=mode, payload_json="{}", expires_at=expires_at)
        existing.storage_mode = mode
        existing.payload_json = json.dumps(payload)
        existing.expires_at = expires_at
        self.db.add(existing)
        self.db.commit()

    def _normalize_payload(
        self,
        endpoint_type: str,
        payload: dict[str, Any],
        compatibilities: list[str],
        model_name: str | None,
    ) -> dict[str, Any]:
        normalized = dict(payload)
        compat_set = {item.lower() for item in compatibilities}
        normalized.setdefault("model", model_name or payload.get("model") or "gpt-4o-mini")

        if "gemini" in compat_set and "contents" in payload and "messages" not in payload:
            messages = []
            for entry in payload.get("contents", []):
                parts = entry.get("parts", []) if isinstance(entry, dict) else []
                text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
                role = entry.get("role", "user") if isinstance(entry, dict) else "user"
                messages.append({"role": role, "content": text})
            normalized["messages"] = messages

        if "anthropic" in compat_set and isinstance(payload.get("messages"), list):
            messages = []
            for message in payload["messages"]:
                if isinstance(message, dict) and isinstance(message.get("content"), list):
                    text = "".join(
                        item.get("text", "") for item in message["content"] if isinstance(item, dict)
                    )
                    messages.append({"role": message.get("role", "user"), "content": text})
                else:
                    messages.append(message)
            normalized["messages"] = messages

        if endpoint_type == "completion" and "prompt" not in normalized and normalized.get("messages"):
            normalized["prompt"] = "\n".join(
                item.get("content", "") for item in normalized["messages"] if isinstance(item, dict)
            )

        return normalized

    def log_request(
        self,
        endpoint_path: str,
        provider_slug: str | None,
        status_code: int,
        latency_ms: int,
        cache_hit: bool,
        failover_used: bool,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        error_type: str | None = None,
    ) -> None:
        request_hash = stable_hash(request_payload)
        self.db.add(
            RequestLog(
                endpoint_path=endpoint_path,
                provider_slug=provider_slug,
                request_hash=request_hash,
                status_code=status_code,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                failover_used=failover_used,
                error_type=error_type,
                request_excerpt=json.dumps(request_payload)[:800],
                response_excerpt=json.dumps(response_payload)[:1200],
            )
        )
        self.db.commit()

    async def execute(
        self,
        endpoint_type: str,
        compatibilities: list[str],
        provider_order: list[str],
        payload: dict[str, Any],
        request_path: str,
        cache_enabled: bool,
        cache_mode: str,
        cache_ttl_seconds: int,
        model_name: str | None = None,
    ) -> dict[str, Any]:
        normalized_payload = self._normalize_payload(endpoint_type, payload, compatibilities, model_name)
        cache_key = stable_hash({"path": request_path, "payload": normalized_payload, "providers": provider_order, "compat": compatibilities})
        if cache_enabled:
            cached = self._read_cache(cache_key, cache_mode)
            if cached:
                self.log_request(request_path, cached.get("_provider"), 200, 0, True, False, normalized_payload, cached)
                return cached

        last_error = None
        configs = self._load_provider_configs(provider_order)
        if not configs:
            raise HTTPException(status_code=400, detail="No enabled providers configured for this route.")

        for index, provider in enumerate(configs):
            runtime = self._runtime_config(provider)
            if not runtime:
                continue
            started = datetime.utcnow()
            try:
                result = await self.invoker.invoke(runtime, endpoint_type, normalized_payload)
                result["_provider"] = provider.slug
                latency_ms = int((datetime.utcnow() - started).total_seconds() * 1000)
                self.log_request(request_path, provider.slug, 200, latency_ms, False, index > 0, normalized_payload, result)
                if cache_enabled:
                    self._write_cache(cache_key, cache_mode, result, cache_ttl_seconds)
                provider.health_status = "healthy"
                self.db.add(provider)
                self.db.commit()
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                provider.health_status = "degraded"
                self.db.add(provider)
                self.db.commit()

        failure = {"error": "All providers failed.", "detail": last_error or "No provider API keys configured."}
        self.log_request(request_path, None, 502, 0, False, True, normalized_payload, failure, error_type="provider_failure")
        raise HTTPException(status_code=502, detail=failure)


def dashboard_summary(db: Session) -> dict[str, Any]:
    total_requests = db.scalar(select(func.count(RequestLog.id))) or 0
    requests_today = db.scalar(select(func.count(RequestLog.id)).where(RequestLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))) or 0
    providers = db.scalars(select(Provider)).all()
    endpoints = db.scalars(select(Endpoint)).all()
    failed_requests = db.scalar(select(func.count(RequestLog.id)).where(RequestLog.status_code >= 400)) or 0
    cache_hits = db.scalar(select(func.count(RequestLog.id)).where(RequestLog.cache_hit.is_(True))) or 0
    failovers = db.scalar(select(func.count(RequestLog.id)).where(RequestLog.failover_used.is_(True))) or 0
    avg_latency = db.scalar(select(func.avg(RequestLog.latency_ms))) or 0
    recent_logs = db.scalars(select(RequestLog).order_by(RequestLog.created_at.desc()).limit(20)).all()
    return {
        "activeProviders": sum(1 for provider in providers if provider.enabled),
        "requestsToday": requests_today,
        "requestsThisMonth": total_requests,
        "averageResponseTime": round(float(avg_latency), 2),
        "failedRequests": failed_requests,
        "runningEndpoints": sum(1 for endpoint in endpoints if endpoint.enabled),
        "cacheHitRate": round((cache_hits / total_requests) * 100, 2) if total_requests else 0,
        "failoverEvents": failovers,
        "requestSeries": [{"label": log.created_at.strftime("%H:%M"), "requests": 1} for log in reversed(recent_logs)],
        "latencySeries": [{"label": log.created_at.strftime("%H:%M"), "latency": log.latency_ms} for log in reversed(recent_logs)],
        "providerHealth": [{"name": provider.display_name, "status": provider.health_status} for provider in providers[:12]],
        "recentActivity": [
            {
                "endpoint": log.endpoint_path,
                "provider": log.provider_slug,
                "statusCode": log.status_code,
                "latencyMs": log.latency_ms,
                "cacheHit": log.cache_hit,
                "createdAt": log.created_at.isoformat(),
            }
            for log in recent_logs[:10]
        ],
    }


def docs_payload(db: Session) -> dict[str, Any]:
    base_url = f"http://{settings.app_host}:{settings.app_port}"
    endpoints = [serialize_endpoint(item) for item in db.scalars(select(Endpoint).order_by(Endpoint.path)).all()]
    providers = [serialize_provider(item) for item in db.scalars(select(Provider).order_by(Provider.display_name)).all()]
    return {
        "sections": [
            {"title": "Install", "content": ["git clone <repo>", "pip install -r requirements.txt", "python main.py"]},
            {"title": "Local Gateway", "content": [f"{item['method']} {item['path']}" for item in endpoints]},
            {"title": "Providers", "content": [f"{item['displayName']} ({item['slug']})" for item in providers]},
            {"title": "Examples", "content": [f'curl -X POST {base_url}/v1/chat/completions -H "Content-Type: application/json" -d "{{\\"model\\": \\"gpt-4o-mini\\", \\"messages\\": [{{\\"role\\": \\"user\\", \\"content\\": \\"Hello\\"}}]}}"']},
            {"title": "Port Note", "content": ["If a request to localhost:8000 returns an SSL or unrelated service error, another app owns that port. Start AI-Translator on a free port or call the port shown in the AI-Translator console."]},
        ]
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _command_block(commands: dict[str, str]) -> str:
    rows = []
    for label, command in commands.items():
        rows.extend([f"## {label}", "```bash", command, "```", ""])
    return "\n".join(rows).strip()


def _binary_build_metadata(target: str) -> dict[str, Any]:
    if target == "windows-exe":
        return {
            "platform": "Windows",
            "artifact_glob": "*.exe",
            "build_command": f'"{sys.executable}" -m PyInstaller --noconfirm --clean --distpath dist --workpath build "{ROOT_DIR / "api_translate.spec"}"',
        }
    if target == "linux-binary":
        return {
            "platform": "Linux",
            "artifact_glob": "*",
            "build_command": f'"{sys.executable}" -m PyInstaller --noconfirm --clean --onefile --name ai-translator --distpath dist --workpath build "{ROOT_DIR / "main.py"}"',
        }
    return {
        "platform": "Darwin",
        "artifact_glob": "*.app",
        "build_command": f'"{sys.executable}" -m PyInstaller --noconfirm --clean --windowed --name AI-Translator --distpath dist --workpath build "{ROOT_DIR / "main.py"}"',
    }


def _resolve_bundle_output(target: str, output_dir: str | None) -> tuple[Path, Path | None]:
    if not output_dir:
        bundle_dir = EXPORTS_DIR / f"{target}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return bundle_dir, None

    requested_path = Path(str(output_dir)).expanduser()
    if target == "windows-exe":
        if requested_path.suffix.lower() == ".exe":
            return requested_path.parent, requested_path
        return requested_path, requested_path / "AI-Translator.exe"
    return requested_path, None


def _generate_binary_bundle(bundle_dir: Path, target: str, requested_artifact_path: Path | None = None) -> dict[str, Any]:
    metadata = _binary_build_metadata(target)
    current_platform = platform.system()
    commands = {
        "Install Dependencies": "pip install -r requirements.txt",
        "Build Command": metadata["build_command"],
        "Run Locally": "python main.py",
    }
    info: dict[str, Any] = {
        "kind": "binary",
        "targetPlatform": metadata["platform"],
        "currentPlatform": current_platform,
        "commands": commands,
        "artifactPath": None,
        "built": False,
        "reason": "",
    }

    if shutil.which("pyinstaller") is None:
        probe = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], capture_output=True, text=True, cwd=ROOT_DIR)
        if probe.returncode != 0:
            info["reason"] = "PyInstaller is not installed in this environment."
            return info

    if current_platform != metadata["platform"]:
        info["reason"] = f"This machine is {current_platform}. Build this target on {metadata['platform']}."
        return info

    temp_root = bundle_dir / ".pyinstaller"
    dist_dir = temp_root / "dist"
    work_dir = temp_root / "build"
    spec_or_entry = ROOT_DIR / "api_translate.spec" if target == "windows-exe" else ROOT_DIR / "main.py"
    build_command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist_dir), "--workpath", str(work_dir)]
    if target == "windows-exe":
        build_command.append(str(spec_or_entry))
    elif target == "linux-binary":
        build_command.extend(["--onefile", "--name", "ai-translator", str(spec_or_entry)])
    else:
        build_command.extend(["--windowed", "--name", "AI-Translator", str(spec_or_entry)])

    try:
        result = subprocess.run(build_command, capture_output=True, text=True, cwd=ROOT_DIR, timeout=900)
    except subprocess.TimeoutExpired:
        info["reason"] = "PyInstaller build timed out after 15 minutes."
        return info
    except Exception as exc:  # noqa: BLE001
        info["reason"] = f"PyInstaller build could not start: {exc}"
        return info
    _write_text(bundle_dir / "pyinstaller-build.log", result.stdout + "\n\n" + result.stderr)

    if result.returncode != 0:
        info["reason"] = "PyInstaller build failed. See pyinstaller-build.log."
        return info

    candidates = [path for path in dist_dir.rglob("*") if path.is_file() or path.suffix == ".app"]
    artifact = next((path for path in candidates if path.match(metadata["artifact_glob"]) or path.suffix == ".app"), None)
    if artifact:
        final_artifact = artifact
        if requested_artifact_path:
            requested_artifact_path.parent.mkdir(parents=True, exist_ok=True)
            if requested_artifact_path.exists():
                requested_artifact_path.unlink()
            shutil.copy2(artifact, requested_artifact_path)
            final_artifact = requested_artifact_path
        shutil.rmtree(temp_root, ignore_errors=True)
        info["artifactPath"] = str(final_artifact)
        info["built"] = True
        return info

    info["reason"] = "Build completed but no packaged artifact was found."
    return info


def _setup_commands_for_target(target: str) -> dict[str, str]:
    base = {
        "Install": "pip install -r requirements.txt",
        "Build Frontend": "cd frontend && npm install && npm run build",
        "Run App": "python main.py",
    }
    extras: dict[str, str] = {}
    if target in {"windows-exe", "linux-binary", "macos-app"}:
        extras = {
            "Build Artifact": _binary_build_metadata(target)["build_command"],
        }
    elif target == "docker":
        extras = {
            "Build Image": "docker compose build",
            "Start Container": "docker compose up -d",
        }
    elif target == "render":
        extras = {
            "Build Command": "pip install -r requirements.txt && cd frontend && npm install && npm run build",
            "Start Command": "python main.py --host 0.0.0.0 --port $PORT",
        }
    elif target == "railway":
        extras = {
            "Build Command": "pip install -r requirements.txt && cd frontend && npm install && npm run build",
            "Start Command": "python main.py --host 0.0.0.0 --port $PORT",
        }
    elif target == "flyio":
        extras = {
            "Launch": "fly launch",
            "Deploy": "fly deploy",
        }
    elif target == "vps":
        extras = {
            "Create Venv": "python -m venv .venv && .venv\\Scripts\\activate",
            "Run Service": "python main.py --host 0.0.0.0 --port 8000",
        }
    elif target == "vercel":
        extras = {
            "Install Vercel CLI": "npm install -g vercel",
            "Deploy": "vercel --prod",
        }
    elif target == "cloudflare-workers":
        extras = {
            "Install Wrangler": "npm install -g wrangler",
            "Deploy": "wrangler deploy",
        }
    elif target == "netlify":
        extras = {
            "Install Netlify CLI": "npm install -g netlify-cli",
            "Deploy": "netlify deploy --prod",
        }
    return {**base, **extras}


def _write_target_files(bundle_dir: Path, target: str, commands: dict[str, str], config: dict[str, Any]) -> None:
    if target == "docker":
        _write_text(
            bundle_dir / "Dockerfile",
            "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nRUN cd frontend && npm install && npm run build\nCMD [\"python\", \"main.py\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n",
        )
        _write_text(
            bundle_dir / "docker-compose.yml",
            "version: \"3.9\"\nservices:\n  ai-translator:\n    build: .\n    ports:\n      - \"8000:8000\"\n    restart: unless-stopped\n",
        )
    elif target == "render":
        _write_text(
            bundle_dir / "render.yaml",
            textwrap.dedent(
                """
                services:
                  - type: web
                    name: ai-translator
                    env: python
                    buildCommand: pip install -r requirements.txt && cd frontend && npm install && npm run build
                    startCommand: python main.py --host 0.0.0.0 --port $PORT
                """
            ).strip() + "\n",
        )
    elif target == "railway":
        _write_text(
            bundle_dir / "railway.json",
            json.dumps(
                {
                    "$schema": "https://railway.app/railway.schema.json",
                    "build": {"builder": "NIXPACKS"},
                    "deploy": {"startCommand": "python main.py --host 0.0.0.0 --port $PORT"},
                },
                indent=2,
            ),
        )
    elif target == "flyio":
        _write_text(
            bundle_dir / "fly.toml",
            textwrap.dedent(
                """
                app = "ai-translator"
                [build]
                [http_service]
                  internal_port = 8000
                  force_https = true
                  auto_start_machines = true
                  auto_stop_machines = true
                """
            ).strip() + "\n",
        )
    elif target == "vps":
        _write_text(
            bundle_dir / "ai-translator.service",
            textwrap.dedent(
                f"""
                [Unit]
                Description=AI-Translator
                After=network.target

                [Service]
                WorkingDirectory={ROOT_DIR}
                ExecStart={sys.executable} {ROOT_DIR / "main.py"} --host 0.0.0.0 --port 8000
                Restart=always

                [Install]
                WantedBy=multi-user.target
                """
            ).strip() + "\n",
        )
    elif target == "vercel":
        _write_text(
            bundle_dir / "vercel.json",
            json.dumps(
                {
                    "version": 2,
                    "builds": [{"src": "api/index.py", "use": "@vercel/python"}],
                    "routes": [{"src": "/(.*)", "dest": "api/index.py"}],
                },
                indent=2,
            ),
        )
        _write_text(bundle_dir / "api" / "index.py", "from app.main import create_app\napp = create_app()\n")
    elif target == "cloudflare-workers":
        _write_text(bundle_dir / "wrangler.toml", 'name = "ai-translator"\nmain = "worker.js"\ncompatibility_date = "2026-05-30"\n')
        _write_text(bundle_dir / "worker.js", "export default { async fetch() { return new Response('Configure your upstream AI-Translator deployment before using Workers.'); } };\n")
    elif target == "netlify":
        _write_text(bundle_dir / "netlify.toml", "[build]\ncommand = \"pip install -r requirements.txt && cd frontend && npm install && npm run build\"\npublish = \"frontend/dist\"\n")
        _write_text(bundle_dir / "netlify" / "functions" / "app.py", "from app.main import create_app\napp = create_app()\n")

    _write_text(bundle_dir / "COMMANDS.md", _command_block(commands) + "\n")
    _write_text(
        bundle_dir / "SETUP.md",
        textwrap.dedent(
            f"""
            # {target} setup

            Flow path: {config.get('flowPath') or 'not selected'}
            Endpoint style: {config.get('endpointStyle') or 'openai'}
            Dashboard protection: {"enabled" if config.get('dashboardAuthEnabled') else "disabled"}

            {_command_block(commands)}
            """
        ).strip() + "\n",
    )


def create_deployment_bundle(target: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or {}
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    bundle_dir, requested_artifact_path = _resolve_bundle_output(target, config.get("outputDir"))
    bundle_dir.mkdir(parents=True, exist_ok=True)

    commands = _setup_commands_for_target(target)
    build_info: dict[str, Any] | None = None
    if target in {"windows-exe", "linux-binary", "macos-app"} and config.get("autoBuild"):
        build_info = _generate_binary_bundle(bundle_dir, target, requested_artifact_path=requested_artifact_path)
        commands = build_info["commands"]
    elif target in {"windows-exe", "linux-binary", "macos-app"}:
        build_info = {
            "kind": "binary",
            "targetPlatform": _binary_build_metadata(target)["platform"],
            "currentPlatform": platform.system(),
            "commands": _setup_commands_for_target(target),
            "artifactPath": None,
            "built": False,
            "reason": "Auto-build is off. Use the generated build command in this bundle to create the artifact manually.",
        }
        commands = build_info["commands"]
    _write_target_files(bundle_dir, target, commands, config)

    readme_sections = [
        f"# {target} export",
        "",
        "This folder is generated by AI-Translator.",
        f"Flow: {config.get('flowPath') or 'not selected'}",
        f"Endpoint style: {config.get('endpointStyle') or 'openai'}",
        f"Dashboard protection: {'enabled' if config.get('dashboardAuthEnabled') else 'disabled'}",
        "",
        "## Setup commands",
        _command_block(commands),
    ]
    if build_info:
        readme_sections.extend(
            [
                "",
                "## Binary build status",
                f"- Built: {build_info['built']}",
                f"- Target platform: {build_info['targetPlatform']}",
                f"- Current platform: {build_info['currentPlatform']}",
                f"- Artifact: {build_info['artifactPath'] or 'not generated'}",
                f"- Note: {build_info['reason'] or 'Binary build completed.'}",
            ]
        )
    _write_text(bundle_dir / "README.md", "\n".join(readme_sections).strip() + "\n")
    _write_text(bundle_dir / "build-config.json", json.dumps(config, indent=2))

    manifest = {"target": target, "path": str(bundle_dir), "config": config, "build": build_info, "commands": commands}
    return manifest


def minimal_status_html(db: Session) -> str:
    summary = dashboard_summary(db)
    endpoint_rows = "".join(
        f"<li><strong>{item.path}</strong> ({item.method})</li>" for item in db.scalars(select(Endpoint).order_by(Endpoint.path)).all()
    )
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>AI-Translator Minimal Mode</title>
  <style>
    body {{ background:#09090b; color:#f4f4f5; font-family:Arial,sans-serif; margin:0; padding:32px; }}
    .card {{ background:#18181b; border:1px solid #27272a; border-radius:20px; padding:24px; margin-bottom:16px; }}
    ul {{ padding-left:20px; }}
  </style>
</head>
<body>
  <div class="card"><h1>AI-Translator Minimal Mode</h1><p>Gateway is running without the React dashboard.</p></div>
  <div class="card"><h2>Summary</h2><p>Providers: {summary["activeProviders"]} | Endpoints: {summary["runningEndpoints"]} | Requests today: {summary["requestsToday"]}</p></div>
  <div class="card"><h2>Endpoints</h2><ul>{endpoint_rows}</ul></div>
</body>
</html>
"""
