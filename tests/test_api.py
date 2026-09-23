"""End-to-end route tests against a fake backend."""
from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["backend"] == "fake"
    assert body["backend_healthy"] is True


def test_models_lists_voices(client):
    r = client.get("/v1/models")
    assert r.status_code == 200
    ids = [m["id"] for m in r.json()["data"]]
    assert "nadeko" in ids


def test_speech_wav_oneshot(client):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "Hallo Welt.", "voice": "nadeko", "response_format": "wav"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content.startswith(b"RIFF") and b"WAVE" in r.content[:20]


def test_speech_pcm_oneshot(client):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "Hallo Welt.", "voice": "nadeko", "response_format": "pcm"},
    )
    assert r.status_code == 200
    # 100ms silence at 24kHz mono s16 = 4800 bytes per synth call, 1 chunk
    assert len(r.content) == 4800


def test_speech_multiple_sentences_produces_more_audio(client):
    r = client.post(
        "/v1/audio/speech",
        json={
            "input": "Hallo Welt. Wie geht es dir? Es ist ein schöner Tag.",
            "voice": "nadeko",
            "response_format": "pcm",
        },
    )
    assert r.status_code == 200
    # 3 sentences = 3 chunks * 100ms = 14400 bytes + 2 gaps
    assert len(r.content) > 4800 * 3


def test_speech_unknown_voice_400(client):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "hi", "voice": "does-not-exist"},
    )
    assert r.status_code == 400


def test_speech_empty_input_400(client):
    r = client.post("/v1/audio/speech", json={"input": ""})
    assert r.status_code == 400


def test_speech_bad_format_400(client):
    r = client.post(
        "/v1/audio/speech",
        json={"input": "hi", "response_format": "ogg"},
    )
    assert r.status_code == 400
