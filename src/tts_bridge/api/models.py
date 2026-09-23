"""`/v1/models` route — returns voice presets as models for OpenAI-client compat."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..voices import VoiceRegistry
from .deps import get_voices
from .schemas import Model, ModelList

router = APIRouter()


@router.get("/v1/models")
def list_models(voices: VoiceRegistry = Depends(get_voices)) -> ModelList:
    return ModelList(data=[Model(id=name) for name in voices.names()])
