from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Body, Cookie, Depends, FastAPI, Header, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal, get_db
from app.models import DeploymentTarget, Endpoint, Provider, RequestLog, Setting
from app.providers import SUPPORTED_ENDPOINTS, catalog_lookup
from app.schemas import (
    DeploymentPayload,
    EndpointClonePayload,
    EndpointDeletePayload,
    EndpointPayload,
    LoginPayload,
    ProviderPayload,
    ProviderRemovePayload,
    SecretPayload,
    SettingsPayload,
    TestGatewayPayload,
)
from app.services import (
    AuthService,
    GatewayService,
    create_deployment_bundle,
    dashboard_summary,
    docs_payload,
    ensure_default_state,
    generate_endpoint_preview,
    get_catalog,
    get_env_values,
    mask_secret,
    serialize_endpoint,
    serialize_provider,
    write_env_value,
)


router = APIRouter(prefix="/api")
registered_dynamic_routes: set[str] = set()


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="api_translate_session"),
    csrf_cookie: str | None = Cookie(default=None, alias="api_translate_csrf"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> bool:
    auth = AuthService(db)
    if not auth.verify_session(session_token):
        raise HTTPException(status_code=401, detail="Authentication required.")
    if auth.is_dashboard_protected() and request and request.method not in {"GET", "HEAD", "OPTIONS"}:
        if csrf_cookie and csrf_cookie != csrf_header:
            raise HTTPException(status_code=403, detail="Invalid CSRF token.")
    return True


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_default_state(db)
    return {"status": "ok", "database": "ready", "providersConfigured": db.query(Provider).count()}


@router.get("/dashboard/summary")
def dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_default_state(db)
    return dashboard_summary(db)


@router.get("/providers/catalog")
def provider_catalog() -> dict[str, Any]:
    return {"items": get_catalog()}


@router.get("/providers/list")
def providers_list(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_default_state(db)
    items = db.scalars(select(Provider).order_by(Provider.priority.desc(), Provider.display_name)).all()
    return {"items": [serialize_provider(item) for item in items]}


@router.post("/providers/add")
def providers_add(payload: ProviderPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    ensure_default_state(db)
    template = catalog_lookup(payload.provider) or {}
    record = db.scalar(select(Provider).where(Provider.slug == payload.provider))
    if record:
        raise HTTPException(status_code=409, detail="Provider already exists.")
    env_var = template.get("env_var", f"{payload.provider.upper()}_API_KEY")
    record = Provider(
        slug=payload.provider,
        display_name=payload.displayName,
        env_var=env_var,
        base_url=payload.baseUrl or template.get("base_url", ""),
        transport=template.get("transport", "openai_compatible"),
        default_model=payload.defaultModel,
        enabled=payload.enabled,
        priority=payload.priority,
        timeout_seconds=payload.timeoutSeconds,
        max_retries=payload.maxRetries,
        metadata_json=json.dumps(payload.metadata),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    if payload.apiKey:
        write_env_value(record.env_var, payload.apiKey)
    return {"item": serialize_provider(record)}


@router.post("/providers/update")
def providers_update(payload: ProviderPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    record = db.scalar(select(Provider).where(Provider.slug == payload.provider))
    if not record:
        raise HTTPException(status_code=404, detail="Provider not found.")
    record.display_name = payload.displayName
    record.base_url = payload.baseUrl or record.base_url
    record.default_model = payload.defaultModel
    record.enabled = payload.enabled
    record.priority = payload.priority
    record.timeout_seconds = payload.timeoutSeconds
    record.max_retries = payload.maxRetries
    record.metadata_json = json.dumps(payload.metadata)
    db.add(record)
    db.commit()
    db.refresh(record)
    if payload.apiKey:
        write_env_value(record.env_var, payload.apiKey)
    return {"item": serialize_provider(record)}


@router.delete("/providers/remove")
def providers_remove(payload: ProviderRemovePayload = Body(...), db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    record = db.scalar(select(Provider).where(Provider.slug == payload.slug))
    if not record:
        raise HTTPException(status_code=404, detail="Provider not found.")
    db.delete(record)
    db.commit()
    return {"status": "removed", "slug": payload.slug}


@router.post("/keys/save")
def save_key(payload: SecretPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    provider = db.scalar(select(Provider).where(Provider.slug == payload.provider))
    env_var = payload.envVar or (provider.env_var if provider else f"{payload.provider.upper()}_API_KEY")
    write_env_value(env_var, payload.apiKey)
    return {"provider": payload.provider, "envVar": env_var, "maskedKey": mask_secret(payload.apiKey)}


@router.get("/keys/list")
def keys_list(db: Session = Depends(get_db)) -> dict[str, Any]:
    env_values = get_env_values()
    items = []
    for provider in db.scalars(select(Provider).order_by(Provider.display_name)).all():
        items.append(
            {
                "provider": provider.slug,
                "displayName": provider.display_name,
                "envVar": provider.env_var,
                "maskedKey": mask_secret(env_values.get(provider.env_var)),
            }
        )
    return {"items": items}


@router.get("/endpoints/list")
def endpoints_list(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_default_state(db)
    items = db.scalars(select(Endpoint).order_by(Endpoint.updated_at.desc(), Endpoint.name)).all()
    return {"items": [serialize_endpoint(item) for item in items]}


@router.post("/endpoints/generate")
def endpoints_generate(
    request: Request,
    payload: EndpointPayload,
    db: Session = Depends(get_db),
    _: bool = Depends(require_admin),
) -> dict[str, Any]:
    blocks = payload.blocks
    record = db.scalar(select(Endpoint).where(Endpoint.path == payload.path))
    if not record:
        record = Endpoint(path=payload.path, method=payload.method)
    record.name = payload.name
    record.method = payload.method
    record.category = payload.category
    record.summary = payload.summary
    record.endpoint_type = payload.endpointType
    record.compatibility_json = json.dumps(payload.compatibilities)
    record.model_name = payload.modelName
    record.blockly_json = json.dumps(blocks)
    record.generated_code = generate_endpoint_preview(
        payload.path,
        payload.method,
        blocks,
        payload.endpointType,
        payload.compatibilities,
        payload.modelName,
    )
    record.provider_order_json = json.dumps(payload.providerOrder)
    record.auth_mode = payload.authMode
    record.cache_enabled = payload.cacheEnabled
    record.cache_mode = payload.cacheMode
    record.cache_ttl_seconds = payload.cacheTtlSeconds
    record.rate_limit_per_minute = payload.rateLimitPerMinute
    record.enabled = True
    db.add(record)
    db.commit()
    db.refresh(record)
    if record.path not in registered_dynamic_routes:
        def dynamic_handler_factory(path: str):
            async def handler(inner_request: Request, inner_db: Session = Depends(get_db)):
                endpoint = inner_db.scalar(select(Endpoint).where(Endpoint.path == path, Endpoint.enabled.is_(True)))
                if not endpoint:
                    raise HTTPException(status_code=404, detail="Endpoint not found.")
                body = await inner_request.json()
                gateway = GatewayService(inner_db)
                return await gateway.execute(
                    endpoint_type=endpoint.endpoint_type if endpoint.path not in SUPPORTED_ENDPOINTS else SUPPORTED_ENDPOINTS.get(path, "chat"),
                    compatibilities=json.loads(endpoint.compatibility_json or '["openai"]'),
                    provider_order=json.loads(endpoint.provider_order_json or "[]"),
                    payload=body,
                    request_path=path,
                    cache_enabled=endpoint.cache_enabled,
                    cache_mode=endpoint.cache_mode,
                    cache_ttl_seconds=endpoint.cache_ttl_seconds,
                    model_name=endpoint.model_name,
                )

            return handler

        request.app.add_api_route(record.path, dynamic_handler_factory(record.path), methods=[record.method])
        registered_dynamic_routes.add(record.path)
    return {"item": serialize_endpoint(record)}


@router.delete("/endpoints/remove")
def endpoints_remove(payload: EndpointDeletePayload = Body(...), db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    record = db.scalar(select(Endpoint).where(Endpoint.id == payload.id))
    if not record:
        raise HTTPException(status_code=404, detail="Endpoint not found.")
    db.delete(record)
    db.commit()
    return {"status": "removed", "id": payload.id}


@router.post("/endpoints/clone")
def endpoints_clone(payload: EndpointClonePayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    record = db.scalar(select(Endpoint).where(Endpoint.id == payload.id))
    if not record:
        raise HTTPException(status_code=404, detail="Endpoint not found.")

    cloned_path = payload.path or f"{record.path}-copy"
    existing = db.scalar(select(Endpoint).where(Endpoint.path == cloned_path))
    if existing:
        raise HTTPException(status_code=409, detail="Target path already exists.")

    clone = Endpoint(
        name=payload.name or f"{record.name} Copy",
        path=cloned_path,
        method=record.method,
        category=record.category,
        summary=record.summary,
        endpoint_type=record.endpoint_type,
        compatibility_json=record.compatibility_json,
        model_name=record.model_name,
        blockly_json=record.blockly_json,
        generated_code=record.generated_code,
        provider_order_json=record.provider_order_json,
        auth_mode=record.auth_mode,
        cache_enabled=record.cache_enabled,
        cache_mode=record.cache_mode,
        cache_ttl_seconds=record.cache_ttl_seconds,
        rate_limit_per_minute=record.rate_limit_per_minute,
        enabled=True,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return {"item": serialize_endpoint(clone)}


@router.post("/gateway/test")
async def gateway_test(payload: TestGatewayPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    gateway = GatewayService(db)
    return await gateway.execute(
        endpoint_type=payload.endpointType,
        compatibilities=payload.compatibilities,
        provider_order=payload.providerOrder,
        payload=payload.payload,
        request_path=payload.requestPath,
        cache_enabled=payload.cacheEnabled,
        cache_mode=payload.cacheMode,
        cache_ttl_seconds=payload.cacheTtlSeconds,
        model_name=payload.payload.get("model") if isinstance(payload.payload, dict) else None,
    )


@router.get("/logs")
def logs_list(db: Session = Depends(get_db), limit: int = 100) -> dict[str, Any]:
    items = db.scalars(select(RequestLog).order_by(RequestLog.created_at.desc()).limit(limit)).all()
    return {
        "items": [
            {
                "id": item.id,
                "endpointPath": item.endpoint_path,
                "providerSlug": item.provider_slug,
                "statusCode": item.status_code,
                "latencyMs": item.latency_ms,
                "cacheHit": item.cache_hit,
                "failoverUsed": item.failover_used,
                "errorType": item.error_type,
                "createdAt": item.created_at.isoformat(),
                "requestExcerpt": item.request_excerpt,
                "responseExcerpt": item.response_excerpt,
            }
            for item in items
        ]
    }


@router.get("/logs/export")
def logs_export(db: Session = Depends(get_db)) -> dict[str, Any]:
    return logs_list(db, limit=500)


@router.post("/auth/login")
def login(payload: LoginPayload, response: Response, db: Session = Depends(get_db)) -> dict[str, Any]:
    tokens = AuthService(db).login(payload.password)
    response.set_cookie("api_translate_session", tokens["session"], httponly=True, samesite="lax")
    response.set_cookie("api_translate_csrf", tokens["csrf"], httponly=False, samesite="lax")
    return {"status": "ok"}


@router.post("/auth/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias="api_translate_session"),
) -> dict[str, Any]:
    AuthService(db).logout(session_token)
    response.delete_cookie("api_translate_session")
    response.delete_cookie("api_translate_csrf")
    return {"status": "ok"}


@router.get("/auth/status")
def auth_status(db: Session = Depends(get_db), session_token: str | None = Cookie(default=None, alias="api_translate_session")) -> dict[str, Any]:
    auth = AuthService(db)
    return {"protected": auth.is_dashboard_protected(), "authenticated": auth.verify_session(session_token)}


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)) -> dict[str, Any]:
    ensure_default_state(db)
    record = db.scalar(select(Setting).limit(1))
    assert record is not None
    return {
        "dashboardAuthEnabled": record.dashboard_auth_enabled,
        "corsOrigins": json.loads(record.cors_origins_json or '["*"]'),
        "defaultTimeoutSeconds": record.default_timeout_seconds,
        "defaultRateLimitPerMinute": record.default_rate_limit_per_minute,
        "endpointStyle": record.endpoint_style,
        "csrfEnabled": record.csrf_enabled,
        "secureHeadersEnabled": record.secure_headers_enabled,
    }


@router.post("/settings")
def update_settings(payload: SettingsPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    record = AuthService(db).update_settings(payload.model_dump())
    return {"item": {"dashboardAuthEnabled": record.dashboard_auth_enabled}}


@router.get("/docs/generated")
def docs_generated(db: Session = Depends(get_db)) -> dict[str, Any]:
    return docs_payload(db)


@router.post("/deployments/build")
def deployments_build(payload: DeploymentPayload, db: Session = Depends(get_db), _: bool = Depends(require_admin)) -> dict[str, Any]:
    manifest = create_deployment_bundle(
        payload.target,
        {
            "flowPath": payload.flowPath,
            "endpointStyle": payload.endpointStyle,
            "dashboardAuthEnabled": payload.dashboardAuthEnabled,
            "password": payload.password,
            "notes": payload.notes,
            "autoBuild": payload.autoBuild,
            "outputDir": payload.outputDir,
        },
    )
    db.add(DeploymentTarget(target_type=payload.target, output_path=manifest["path"], manifest_json=json.dumps(manifest)))
    db.commit()
    return {"manifest": manifest}


def register_dynamic_gateway_routes(app: FastAPI) -> None:
    if getattr(app.state, "dynamic_routes_loaded", False):
        return
    app.state.dynamic_routes_loaded = True

    def build_handler(path: str):
        async def handler(request: Request, db: Session = Depends(get_db)):
            endpoint = db.scalar(select(Endpoint).where(Endpoint.path == path, Endpoint.enabled.is_(True)))
            if not endpoint:
                raise HTTPException(status_code=404, detail="Endpoint not found.")
            payload = await request.json()
            gateway = GatewayService(db)
            return await gateway.execute(
                endpoint_type=endpoint.endpoint_type if endpoint.path not in SUPPORTED_ENDPOINTS else SUPPORTED_ENDPOINTS.get(path, "chat"),
                compatibilities=json.loads(endpoint.compatibility_json or '["openai"]'),
                provider_order=json.loads(endpoint.provider_order_json or "[]"),
                payload=payload,
                request_path=path,
                cache_enabled=endpoint.cache_enabled,
                cache_mode=endpoint.cache_mode,
                cache_ttl_seconds=endpoint.cache_ttl_seconds,
                model_name=endpoint.model_name,
            )

        return handler

    for path in SUPPORTED_ENDPOINTS:
        if path not in registered_dynamic_routes:
            app.add_api_route(path, build_handler(path), methods=["POST"])
            registered_dynamic_routes.add(path)

    with SessionLocal() as db:
        ensure_default_state(db)
        records = db.scalars(select(Endpoint).where(Endpoint.enabled.is_(True))).all()
        for record in records:
            if record.path not in registered_dynamic_routes:
                app.add_api_route(record.path, build_handler(record.path), methods=[record.method])
                registered_dynamic_routes.add(record.path)
