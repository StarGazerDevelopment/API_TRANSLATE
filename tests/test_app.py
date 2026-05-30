from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import create_app
from app import services


client = TestClient(create_app(minimal=True))


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_provider_lifecycle() -> None:
    response = client.post(
        "/api/providers/add",
        json={
            "provider": "openai",
            "displayName": "OpenAI",
            "baseUrl": "https://api.openai.com/v1",
            "defaultModel": "gpt-4o-mini",
            "timeoutSeconds": 60,
            "maxRetries": 2,
            "enabled": True,
            "priority": 1,
            "metadata": {},
        },
    )
    assert response.status_code in {200, 409}

    listing = client.get("/api/providers/list")
    assert listing.status_code == 200
    assert isinstance(listing.json()["items"], list)


def test_endpoint_generation() -> None:
    response = client.post(
        "/api/endpoints/generate",
        json={
            "name": "Test Endpoint",
            "path": "/api/custom",
            "method": "POST",
            "category": "custom",
            "blocks": {"blocks": []},
            "providerOrder": ["openai"],
            "authMode": "public",
            "cacheEnabled": True,
            "cacheMode": "sqlite",
            "cacheTtlSeconds": 300,
            "rateLimitPerMinute": 60,
        },
    )
    assert response.status_code == 200
    assert response.json()["item"]["path"] == "/api/custom"


def test_resolve_windows_bundle_output_paths(tmp_path: Path) -> None:
    bundle_dir, artifact_path = services._resolve_bundle_output("windows-exe", str(tmp_path))
    assert bundle_dir == tmp_path
    assert artifact_path == tmp_path / "AI-Translator.exe"

    requested_file = tmp_path / "Desktop" / "Custom Translator.exe"
    bundle_dir, artifact_path = services._resolve_bundle_output("windows-exe", str(requested_file))
    assert bundle_dir == requested_file.parent
    assert artifact_path == requested_file


def test_generate_windows_bundle_copies_artifact_to_requested_path(tmp_path: Path, monkeypatch) -> None:
    target_artifact = tmp_path / "Desktop" / "AI-Translator.exe"

    def fake_run(command: list[str], capture_output: bool, text: bool, cwd: Path, timeout: int | None = None):
        dist_dir = Path(command[command.index("--distpath") + 1])
        work_dir = Path(command[command.index("--workpath") + 1])
        dist_dir.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "AI-Translator.exe").write_text("binary", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(services.shutil, "which", lambda name: "pyinstaller")
    monkeypatch.setattr(services.platform, "system", lambda: "Windows")
    monkeypatch.setattr(services.subprocess, "run", fake_run)

    result = services._generate_binary_bundle(tmp_path, "windows-exe", requested_artifact_path=target_artifact)

    assert result["built"] is True
    assert result["artifactPath"] == str(target_artifact)
    assert target_artifact.exists()
    assert not (tmp_path / ".pyinstaller").exists()
