"""`/v1/audio/speech` route."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse

from ..audio import SUPPORTED_FORMATS, pcm_to_container, wav_header
from ..backends.base import Backend, BackendError, BackendUnavailable
from ..preprocessing import preprocess
from ..streaming import synth_streamed
from ..voices import Voice, VoiceRegistry
from .deps import get_backend, get_config, get_voices, require_auth
from .schemas import SpeechRequest

log = logging.getLogger(__name__)

router = APIRouter()


def _apply_overrides(voice: Voice, req: SpeechRequest) -> Voice:
    """Return a new Voice with per-request Higgs overrides applied."""
    if not any(v is not None for v in (req.temperature, req.top_p, req.top_k, req.seed)):
        return voice
    h = voice.higgs.model_copy(update={
        k: v for k, v in {
            "temperature": req.temperature,
            "top_p": req.top_p,
            "top_k": req.top_k,
            "seed": req.seed,
        }.items() if v is not None
    })
    return voice.model_copy(update={"higgs": h})


@router.post("/v1/audio/speech")
async def speech(
    req: SpeechRequest,
    backend: Backend = Depends(get_backend),
    voices: VoiceRegistry = Depends(get_voices),
    config=Depends(get_config),
    _auth=Depends(require_auth),
) -> Response:
    fmt = req.response_format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"response_format must be one of {SUPPORTED_FORMATS}")
    if fmt in ("mp3", "aac"):
        # These require external encoder; keep the surface minimal until we ship one.
        raise HTTPException(
            501,
            f"response_format={fmt} not implemented yet — use wav, pcm, flac, or opus",
        )

    voice_name = req.voice or config.default_voice
    voice = voices.get(voice_name)
    if voice is None:
        raise HTTPException(400, f"unknown voice: {voice_name!r} (known: {voices.names()})")
    voice = _apply_overrides(voice, req)

    text = preprocess(req.input, config.preprocessing)
    if not text.strip():
        raise HTTPException(400, "input is empty after preprocessing")

    # For streamable formats (wav, pcm), always emit as chunked-transfer so
    # OpenAI-SDK-based clients using `.with_streaming_response.create()`
    # (e.g. wyoming_openai) start playing audio while later sentences are still
    # rendering. For FLAC/Opus we still need a full container, so those buffer.
    can_stream = config.streaming.enabled and fmt in ("wav", "pcm")
    if can_stream:
        return await _stream_response(text, voice, backend, config, fmt)

    return await _oneshot_response(text, voice, backend, config, fmt)


async def _oneshot_response(text, voice, backend, config, fmt) -> Response:
    """Render everything, return one blob."""
    pcm_chunks = []
    sample_rate = 24000
    try:
        async for chunk in synth_streamed(text, voice, backend, config.streaming):
            pcm_chunks.append(chunk)
        # Sample rate is baked into the backend; we grabbed 24k from Higgs, but let's
        # pull it dynamically by running a probe if empty. For now trust the backend.
    except BackendUnavailable as e:
        log.warning("primary backend unavailable: %s", e)
        raise HTTPException(503, f"tts backend unavailable: {e}") from e
    except BackendError as e:
        raise HTTPException(500, f"tts backend error: {e}") from e

    # We assume mono 24kHz from Higgs. If we ever swap backends, expose SR here.
    sample_rate = 24000
    pcm = b"".join(pcm_chunks)
    body = pcm_to_container(pcm, sample_rate, fmt)
    media_type = {
        "wav": "audio/wav",
        "pcm": "audio/L16",
        "flac": "audio/flac",
        "opus": "audio/ogg",
    }[fmt]
    return Response(content=body, media_type=media_type)


async def _stream_response(text, voice, backend, config, fmt) -> StreamingResponse:
    """Chunked-transfer streaming.

    For `pcm`/`wav`: prepend format header, then yield raw PCM as chunks arrive.
    For `flac`/`opus`: fall back to buffer + one-shot at end (container needs full stream).
    """
    if fmt in ("flac", "opus"):
        # Containers can't be trivially streamed; do a one-shot but under stream=true.
        async def gen():
            data = await _oneshot_response(text, voice, backend, config, fmt)
            yield data.body
        return StreamingResponse(gen(), media_type=data_media(fmt))

    sample_rate = 24000  # Higgs backend fixed rate. Update if backend changes.

    async def gen_wav_or_pcm() -> AsyncIterator[bytes]:
        if fmt == "wav":
            # RIFF size unknown up front for streaming — write a header with the largest
            # legal 32-bit size so players just keep reading until the socket closes.
            # This is the standard trick for streamed WAV.
            yield wav_header(0xFFFFFFFF - 36, sample_rate)
        try:
            async for pcm in synth_streamed(text, voice, backend, config.streaming):
                yield pcm
        except BackendUnavailable as e:
            log.warning("primary backend unavailable mid-stream: %s", e)
            # No good way to signal error mid-body; close gracefully.
            return
        except BackendError:
            return

    return StreamingResponse(gen_wav_or_pcm(), media_type=data_media(fmt))


def data_media(fmt: str) -> str:
    return {"wav": "audio/wav", "pcm": "audio/L16", "flac": "audio/flac", "opus": "audio/ogg"}[fmt]
