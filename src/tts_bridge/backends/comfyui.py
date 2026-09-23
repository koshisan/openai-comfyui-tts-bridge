"""ComfyUI backend — submits Higgs v3 workflows and polls for results."""
from __future__ import annotations

import asyncio
import io
import logging
import time
import uuid

import httpx
import numpy as np
import soundfile as sf

from ..config import ComfyUIConfig
from ..voices import Voice
from .base import Backend, BackendError, BackendUnavailable, SynthResult

log = logging.getLogger(__name__)


class ComfyUIBackend(Backend):
    name = "comfyui"

    def __init__(self, config: ComfyUIConfig, model_choice: str = "higgs-audio-v3-tts-4b"):
        self.config = config
        self.model_choice = model_choice
        self._client_id = str(uuid.uuid4())
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            timeout=config.request_timeout,
        )
        self._sem = asyncio.Semaphore(config.max_concurrent)

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> bool:
        try:
            r = await self._client.get("/system_stats", timeout=5.0)
            return r.status_code == 200
        except (httpx.HTTPError, OSError):
            return False

    def _build_workflow(self, text: str, voice: Voice) -> dict:
        n = self.config.nodes
        p = voice.higgs
        return {
            n.load_model: {
                "class_type": "HiggsV3LoadModel",
                "inputs": {
                    "model": self.model_choice,
                    "dtype": p.dtype,
                    "device": "auto",
                    "attention": p.attention,
                    "download_if_missing": False,
                },
            },
            n.load_audio: {
                "class_type": "LoadAudio",
                "inputs": {"audio": voice.reference_audio},
            },
            n.voice_clone: {
                "class_type": "HiggsV3VoiceClone",
                "inputs": {
                    "higgs_model": [n.load_model, 0],
                    "text": text,
                    "reference_audio": [n.load_audio, 0],
                    "reference_text": voice.reference_text,
                    "max_new_tokens": p.max_new_tokens,
                    "temperature": p.temperature,
                    "top_p": p.top_p,
                    "top_k": p.top_k,
                    "seed": p.seed,
                    "longform_chunking": p.longform_chunking,
                    "words_per_chunk": p.words_per_chunk,
                    "tag_chunk": p.tag_chunk,
                    "pause_between_chunks": p.pause_between_chunks,
                },
            },
            n.save_audio: {
                "class_type": "SaveAudio",
                "inputs": {
                    "audio": [n.voice_clone, 0],
                    "filename_prefix": f"tts_bridge/{uuid.uuid4().hex[:8]}",
                },
            },
        }

    async def synth(self, text: str, voice: Voice) -> SynthResult:
        async with self._sem:
            return await self._synth_one(text, voice)

    async def _synth_one(self, text: str, voice: Voice) -> SynthResult:
        wf = self._build_workflow(text, voice)
        try:
            r = await self._client.post(
                "/prompt",
                json={"prompt": wf, "client_id": self._client_id},
            )
        except httpx.HTTPError as e:
            raise BackendUnavailable(f"ComfyUI submit failed: {e}") from e

        if r.status_code != 200:
            raise BackendError(f"ComfyUI /prompt returned {r.status_code}: {r.text[:400]}")

        prompt_id = r.json().get("prompt_id")
        if not prompt_id:
            raise BackendError(f"ComfyUI /prompt returned no prompt_id: {r.text[:200]}")

        history = await self._await_history(prompt_id)
        status = history.get("status", {})
        if status.get("status_str") != "success":
            # Surface the underlying error message.
            messages = status.get("messages", [])
            for m in messages:
                if isinstance(m, list) and len(m) >= 2 and m[0] == "execution_error":
                    err = m[1].get("exception_message", "")
                    raise BackendError(f"ComfyUI execution_error: {err.strip()}")
            raise BackendError(f"ComfyUI run did not succeed: status={status}")

        node = self.config.nodes.save_audio
        outputs = history.get("outputs", {}).get(node, {}).get("audio", [])
        if not outputs:
            raise BackendError(f"ComfyUI produced no audio (node {node})")

        pcm, sr = await self._download_audio(outputs[0])
        return SynthResult(pcm_s16le=pcm, sample_rate=sr)

    async def _await_history(self, prompt_id: str) -> dict:
        deadline = time.monotonic() + self.config.request_timeout
        while time.monotonic() < deadline:
            try:
                r = await self._client.get(f"/history/{prompt_id}")
            except httpx.HTTPError as e:
                raise BackendUnavailable(f"ComfyUI history poll failed: {e}") from e
            if r.status_code == 200:
                data = r.json()
                if prompt_id in data:
                    return data[prompt_id]
            await asyncio.sleep(self.config.poll_interval)
        raise BackendError(f"ComfyUI history timeout after {self.config.request_timeout}s")

    async def _download_audio(self, output: dict) -> tuple[bytes, int]:
        """Fetch the rendered audio file from ComfyUI and decode to mono PCM s16."""
        try:
            r = await self._client.get(
                "/view",
                params={
                    "filename": output["filename"],
                    "subfolder": output.get("subfolder", ""),
                    "type": output.get("type", "output"),
                },
            )
        except httpx.HTTPError as e:
            raise BackendUnavailable(f"ComfyUI /view fetch failed: {e}") from e
        if r.status_code != 200:
            raise BackendError(f"ComfyUI /view returned {r.status_code}")

        data = io.BytesIO(r.content)
        audio, sr = sf.read(data, always_2d=False, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        # Clip and convert to int16
        audio = np.clip(audio, -1.0, 1.0)
        pcm = (audio * 32767.0).astype(np.int16).tobytes()
        return pcm, int(sr)
