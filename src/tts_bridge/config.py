"""Config loading. YAML + env override."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 7780
    auth_token: str | None = None


class ComfyUINodes(BaseModel):
    load_model: str = "1"
    load_audio: str = "2"
    voice_clone: str = "3"
    save_audio: str = "4"


class ComfyUIConfig(BaseModel):
    base_url: str = "http://localhost:8188"
    request_timeout: float = 180.0
    poll_interval: float = 0.5
    max_concurrent: int = 1
    nodes: ComfyUINodes = Field(default_factory=ComfyUINodes)


class PiperConfig(BaseModel):
    enabled: bool = False
    binary_path: str = "/usr/local/bin/piper"
    model_dir: str = "/models/piper"


class StreamingConfig(BaseModel):
    enabled: bool = True
    sentences_per_chunk: int = 1
    chunk_gap: float = 0.15


class PreprocessingConfig(BaseModel):
    enabled: bool = False


class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    default_backend: str = "comfyui"
    comfyui: ComfyUIConfig = Field(default_factory=ComfyUIConfig)
    piper: PiperConfig = Field(default_factory=PiperConfig)
    streaming: StreamingConfig = Field(default_factory=StreamingConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    default_voice: str = "nadeko"


def _find_config_file(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load config from an explicit path, TTS_BRIDGE_CONFIG env, or search defaults."""
    if config_path is None:
        config_path = os.getenv("TTS_BRIDGE_CONFIG")

    if config_path:
        path = Path(config_path)
    else:
        path = _find_config_file([
            Path("/etc/tts-bridge/config.yaml"),
            Path.cwd() / "config" / "config.yaml",
            Path.cwd() / "config.yaml",
        ])

    data: dict[str, Any] = {}
    if path and path.exists():
        with path.open() as f:
            data = yaml.safe_load(f) or {}

    return AppConfig(**data)
