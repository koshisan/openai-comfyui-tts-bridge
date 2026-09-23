from __future__ import annotations

from pathlib import Path

from tts_bridge.config import load_config
from tts_bridge.voices import load_voices


def test_load_config_defaults(tmp_path):
    # No config file → defaults
    cfg = load_config(tmp_path / "does-not-exist.yaml")
    assert cfg.server.port == 7780
    assert cfg.default_backend == "comfyui"


def test_load_config_from_file(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("""
server:
  port: 9999
default_voice: martin
""")
    cfg = load_config(p)
    assert cfg.server.port == 9999
    assert cfg.default_voice == "martin"


def test_load_voices_from_file(tmp_path):
    p = tmp_path / "voices.yaml"
    p.write_text("""
voices:
  martin:
    reference_audio: martin.wav
    reference_text: hallo
    higgs:
      temperature: 0.5
""")
    voices = load_voices(p)
    v = voices.get("martin")
    assert v is not None
    assert v.reference_audio == "martin.wav"
    assert v.higgs.temperature == 0.5
    # unspecified defaults stay
    assert v.higgs.top_k == 50


def test_example_config_is_valid():
    """The shipped example must parse cleanly against the schema."""
    root = Path(__file__).resolve().parent.parent
    cfg = load_config(root / "config" / "config.example.yaml")
    assert cfg.server.port == 7780
    voices = load_voices(root / "config" / "voices.example.yaml")
    assert "nadeko" in voices.names()
