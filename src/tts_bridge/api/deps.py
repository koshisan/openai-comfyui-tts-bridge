"""FastAPI dependency injection glue."""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from ..backends.base import Backend
from ..config import AppConfig
from ..voices import VoiceRegistry


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_voices(request: Request) -> VoiceRegistry:
    return request.app.state.voices


def get_backend(request: Request) -> Backend:
    return request.app.state.backend


def require_auth(request: Request, config: AppConfig = Depends(get_config)) -> None:
    token = config.server.auth_token
    if not token:
        return
    header = request.headers.get("authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix) or header[len(prefix):] != token:
        raise HTTPException(401, "invalid or missing bearer token")
