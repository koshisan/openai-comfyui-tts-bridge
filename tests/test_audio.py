from __future__ import annotations

import io
import struct

import soundfile as sf

from tts_bridge.audio import pcm_to_container, wav_header


def test_wav_header_size():
    hdr = wav_header(pcm_bytes_length=48000, sample_rate=24000)
    assert hdr[:4] == b"RIFF"
    assert hdr[8:12] == b"WAVE"
    # data chunk size at bytes 40-44
    assert struct.unpack("<I", hdr[40:44])[0] == 48000


def test_pcm_passthrough():
    pcm = b"\x00\x01\x02\x03"
    assert pcm_to_container(pcm, 24000, "pcm") == pcm


def test_wav_roundtrip():
    pcm = b"\x00\x00" * 240  # 10ms of silence at 24kHz
    wav = pcm_to_container(pcm, 24000, "wav")
    data, sr = sf.read(io.BytesIO(wav), always_2d=False)
    assert sr == 24000
    assert len(data) == 240


def test_flac_encodes():
    pcm = b"\x00\x00" * 240
    flac = pcm_to_container(pcm, 24000, "flac")
    assert flac[:4] == b"fLaC"
