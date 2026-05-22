from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config.yaml"
ENV_PATH = ROOT_DIR / ".env"


@dataclass(frozen=True)
class Settings:
    provider: str
    host: str
    port: int
    upstream_base_url: str
    upstream_chat_path: str
    upstream_timeout_seconds: float
    model_aliases: dict[str, str]
    upstream_api_key: str
    use_client_auth: bool


def resolve_config_path() -> Path:
    raw = os.getenv("PROXY_CONFIG", "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path
    return DEFAULT_CONFIG_PATH


def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_upstream_api_key() -> str:
    for name in ("UPSTREAM_API_KEY", "JIUTIAN_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def load_settings(config_path: Path | None = None) -> Settings:
    load_dotenv(ENV_PATH)
    path = config_path or resolve_config_path()

    if not path.is_file():
        raise FileNotFoundError(
            f"Config not found: {path}. Copy from config.examples/ or run .\\use-config.ps1 jiutian"
        )

    raw = _load_yaml(path)
    server = raw.get("server") or {}
    upstream = raw.get("upstream") or {}
    aliases = raw.get("model_aliases") or {}

    chat_path = str(upstream.get("chat_path", "/chat/completions")).strip()
    if not chat_path.startswith("/"):
        chat_path = f"/{chat_path}"

    return Settings(
        provider=str(raw.get("provider", "custom")),
        host=str(server.get("host", "127.0.0.1")),
        port=int(server.get("port", 8787)),
        upstream_base_url=str(upstream.get("base_url", "")).rstrip("/"),
        upstream_chat_path=chat_path,
        upstream_timeout_seconds=float(upstream.get("timeout_seconds", 120)),
        model_aliases={str(k): str(v) for k, v in aliases.items()},
        upstream_api_key=_load_upstream_api_key(),
        use_client_auth=os.getenv("USE_CLIENT_AUTH", "false").strip().lower()
        in ("1", "true", "yes"),
    )
