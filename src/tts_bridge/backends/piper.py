"""Piper CPU fallback — stub. TODO: implement.

Wire this up as a fallback when the primary ComfyUI backend is unreachable.
The class is fully constructable and its methods raise `NotImplementedError`
so the routing logic can be developed and tested without a Piper install.
"""
from __future__ import annotations

from ..config import PiperConfig
from ..voices import Voice
from .base import Backend, SynthResult


class PiperBackend(Backend):
    name = "piper"

    def __init__(self, config: PiperConfig):
        self.config = config

    async def health(self) -> bool:
        # Explicitly report unavailable until implemented so routing prefers ComfyUI.
        return False

    async def synth(self, text: str, voice: Voice) -> SynthResult:
        raise NotImplementedError("PiperBackend.synth is not implemented yet")
