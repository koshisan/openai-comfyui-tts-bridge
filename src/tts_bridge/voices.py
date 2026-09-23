"""Voice preset loading."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class HiggsParams(BaseModel):
    dtype: str = "bf16"
    attention: str = "sdpa"
    temperature: float = 0.8
    top_p: float = 0.95
    top_k: int = 50
    seed: int = 0
    max_new_tokens: int = 2048
    words_per_chunk: int = 45
    pause_between_chunks: float = 0.15
    longform_chunking: bool = True
    tag_chunk: bool = False


class Voice(BaseModel):
    reference_audio: str
    reference_text: str = ""
    higgs: HiggsParams = Field(default_factory=HiggsParams)


class VoiceRegistry(BaseModel):
    voices: dict[str, Voice] = Field(default_factory=dict)

    def get(self, name: str) -> Voice | None:
        return self.voices.get(name)

    def names(self) -> list[str]:
        return list(self.voices.keys())


def _find_voices_file(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def load_voices(voices_path: str | Path | None = None) -> VoiceRegistry:
    """Load voice presets."""
    if voices_path is None:
        voices_path = os.getenv("TTS_BRIDGE_VOICES")

    if voices_path:
        path = Path(voices_path)
    else:
        path = _find_voices_file([
            Path("/etc/tts-bridge/voices.yaml"),
            Path.cwd() / "config" / "voices.yaml",
            Path.cwd() / "voices.yaml",
        ])

    if not path or not path.exists():
        return VoiceRegistry()

    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return VoiceRegistry(**data)
