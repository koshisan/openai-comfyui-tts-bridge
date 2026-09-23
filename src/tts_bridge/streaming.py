"""Sentence-level chunking + parallel synthesis coordination."""
from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import AsyncIterator

from .backends.base import Backend, BackendError
from .config import StreamingConfig
from .voices import Voice

log = logging.getLogger(__name__)

# Sentence boundary: end-punctuation followed by whitespace + capital or newline.
# Keeps abbreviations mostly intact and does not split inside `<|...|>` tags.
_SENT_SPLIT = re.compile(
    r"(?<=[.!?。！？])\s+(?=\S)|"    # end-punct followed by more content
    r"\n{2,}",                       # or paragraph break
)


def split_sentences(text: str) -> list[str]:
    """Cheap sentence splitter tuned for TTS chunking.

    Splits on end-punctuation and paragraph breaks but leaves single-line
    bullet lists intact so a bullet is spoken as one unit.
    """
    text = text.strip()
    if not text:
        return []
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p and p.strip()]
    return parts or [text]


def chunk_sentences(sentences: list[str], per_chunk: int) -> list[str]:
    """Group sentences into chunks of `per_chunk`, joined by a single space."""
    if per_chunk <= 1:
        return sentences
    return [" ".join(sentences[i : i + per_chunk]) for i in range(0, len(sentences), per_chunk)]


async def synth_streamed(
    text: str,
    voice: Voice,
    backend: Backend,
    streaming: StreamingConfig,
) -> AsyncIterator[bytes]:
    """Split `text` into chunks, synth each, yield PCM (mono s16le) in order.

    Chunks are dispatched concurrently but yielded strictly in input order so
    the audio plays back naturally. If any chunk fails the exception propagates.
    """
    sentences = split_sentences(text)
    chunks = chunk_sentences(sentences, streaming.sentences_per_chunk)
    if not chunks:
        return

    # Fan out — one task per chunk. `synth()` is expected to internally throttle
    # concurrency via a semaphore inside the backend.
    tasks = [asyncio.create_task(backend.synth(c, voice)) for c in chunks]

    gap_samples_bytes: bytes | None = None

    try:
        for i, task in enumerate(tasks):
            try:
                res = await task
            except BackendError:
                # Cancel outstanding, re-raise
                for t in tasks[i + 1 :]:
                    t.cancel()
                raise

            if i > 0 and gap_samples_bytes is None:
                # Build a silent gap in the first result's sample rate.
                gap_len = max(0, int(res.sample_rate * streaming.chunk_gap))
                gap_samples_bytes = b"\x00\x00" * gap_len
            if i > 0 and gap_samples_bytes:
                yield gap_samples_bytes
            yield res.pcm_s16le
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
