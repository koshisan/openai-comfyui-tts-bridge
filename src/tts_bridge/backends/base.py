"""Abstract TTS backend."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..voices import Voice


class BackendError(RuntimeError):
    """Backend produced a fatal error mid-request."""


class BackendUnavailable(BackendError):
    """Backend cannot be reached at all — a fallback should be tried."""


@dataclass
class SynthResult:
    """Result of a single-chunk synthesis. `pcm_s16le` is little-endian mono PCM."""
    pcm_s16le: bytes
    sample_rate: int


class Backend(ABC):
    """A TTS engine capable of rendering one text chunk to PCM."""

    name: str

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the backend is reachable and ready."""

    @abstractmethod
    async def synth(self, text: str, voice: Voice) -> SynthResult:
        """Render one chunk of text to PCM using the given voice preset."""
