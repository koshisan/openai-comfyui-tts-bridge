"""Pydantic request/response models mirroring OpenAI TTS API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SpeechRequest(BaseModel):
    """Mirrors `openai.audio.speech.create()`.

    Non-standard fields (documented in README) let you override the workflow
    parameters per-request. Missing fields fall back to the voice preset defaults.
    """
    model: str = "tts-1"                               # ignored, kept for API compat
    input: str
    voice: str | None = None                           # voice preset name
    response_format: str = "wav"                       # wav|pcm|flac|opus
    speed: float = 1.0                                 # accepted, not currently applied
    stream: bool = False                               # True → chunked-transfer streaming

    # Optional per-request overrides (extensions beyond OpenAI's spec)
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    seed: int | None = None


class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "openai-comfyui-tts-bridge"


class ModelList(BaseModel):
    object: str = "list"
    data: list[Model] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    backend: str
    backend_healthy: bool
