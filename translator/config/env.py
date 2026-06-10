"""Carga de variables de entorno desde .env."""

from __future__ import annotations

import os
from pathlib import Path

from translator.config.settings import ENV_PATH

_env_loaded = False


def load_env(path: Path | None = None) -> None:
    """Carga KEY=VALUE desde .env (sobrescribe valores previos en el entorno)."""
    global _env_loaded
    env_path = path or ENV_PATH
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    _env_loaded = True


def ensure_env_loaded() -> None:
    if not _env_loaded:
        load_env()


def get_env(name: str, default: str = "") -> str:
    ensure_env_loaded()
    return os.environ.get(name, default)
