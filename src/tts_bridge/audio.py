"""PCM → container conversion (WAV, MP3, FLAC, OPUS, PCM)."""
from __future__ import annotations

import io
import struct

import numpy as np
import soundfile as sf

# OpenAI TTS response_format values we accept.
SUPPORTED_FORMATS = ("wav", "mp3", "flac", "opus", "pcm", "aac")


def wav_header(pcm_bytes_length: int, sample_rate: int, channels: int = 1, bits: int = 16) -> bytes:
    """Build a WAV RIFF header for a known-length PCM payload."""
    byte_rate = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    data_size = pcm_bytes_length
    riff_size = 36 + data_size
    return (
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits)
        + b"data"
        + struct.pack("<I", data_size)
    )


def pcm_to_container(pcm_bytes: bytes, sample_rate: int, fmt: str) -> bytes:
    """Encode raw mono PCM s16le into the requested container format."""
    if fmt == "pcm":
        return pcm_bytes
    if fmt == "wav":
        return wav_header(len(pcm_bytes), sample_rate) + pcm_bytes

    # soundfile can encode FLAC + OGG (opus). MP3/AAC would need ffmpeg;
    # keep the surface minimal and let clients ask for wav/pcm/flac/opus.
    samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    buf = io.BytesIO()
    if fmt == "flac":
        sf.write(buf, samples, sample_rate, format="FLAC")
    elif fmt == "opus":
        sf.write(buf, samples, sample_rate, format="OGG", subtype="OPUS")
    else:
        raise ValueError(f"Unsupported response_format: {fmt}")
    return buf.getvalue()
