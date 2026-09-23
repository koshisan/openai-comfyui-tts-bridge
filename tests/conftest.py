"""Shared test fixtures."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tts_bridge.backends.base import Backend, SynthResult
from tts_bridge.config import AppConfig
from tts_bridge.main import create_app
from tts_bridge.voices import HiggsParams, Voice, VoiceRegistry


class FakeBackend(Backend):
    name = "fake"

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self.calls: list[tuple[str, str]] = []

    async def health(self) -> bool:
        return True

    async def synth(self, text: str, voice) -> SynthResult:
        self.calls.append((text, voice.reference_audio))
        # 100ms of silence as fake PCM
        n = self.sample_rate // 10
        return SynthResult(pcm_s16le=b"\x00\x00" * n, sample_rate=self.sample_rate)


@pytest.fixture
def voice_registry():
    return VoiceRegistry(
        voices={
            "nadeko": Voice(
                reference_audio="nadeko_24k.wav",
                reference_text="ref",
                higgs=HiggsParams(),
            )
        }
    )


@pytest.fixture
def config():
    return AppConfig()


@pytest.fixture
def app_with_fake(config, voice_registry):
    app = create_app(config=config, voices=voice_registry)
    app.state.backend = FakeBackend()
    return app


@pytest.fixture
def client(app_with_fake):
    with TestClient(app_with_fake) as c:
        yield c
