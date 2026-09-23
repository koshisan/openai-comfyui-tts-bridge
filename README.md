# openai-comfyui-tts-bridge

OpenAI-compatible TTS API that routes to a ComfyUI backend running the
[Higgs Audio v3 TTS ComfyUI node](https://github.com/Saganaki22/Higgs_v3-TTS-ComfyUI).
Designed as a drop-in TTS backend for Home Assistant via
[wyoming_openai](https://github.com/roryeckel/wyoming_openai).

## Features

- **OpenAI-compatible `/v1/audio/speech`** — same request shape as `openai.audio.speech.create()`,
  works with any client that already speaks the OpenAI TTS protocol.
- **ComfyUI backend** — submits Higgs v3 workflows to a running ComfyUI instance,
  polls history, returns the rendered audio.
- **Sentence-level streaming** — long text is split at sentence boundaries and
  chunks are generated in parallel so first audio arrives before the last chunk finishes.
- **Voice presets** — named voices (ref clip + transcript + defaults) in `voices.yaml`,
  selectable via the OpenAI `voice` field.
- **Web UI** — minimal HTML page for interactive testing and parameter tuning.

Two extension points are wired up but not yet implemented (planned):

- **Piper CPU fallback** (`PiperBackend`) — kicks in when ComfyUI is unreachable.
- **Text preprocessing pipeline** — emoji stripping, markdown flattening, number-to-words,
  custom regex rules. Currently a no-op passthrough.

## Quick start

```bash
docker compose up -d
```

`tts-bridge` listens on port **7780** and speaks the OpenAI-compatible HTTP API.

## Home Assistant integration

Home Assistant does not talk this API directly — its **Wyoming Protocol**
integration expects a TCP Wyoming server. Bridge the two with
[roryeckel/wyoming_openai](https://github.com/roryeckel/wyoming_openai),
running either as a Home Assistant add-on or as its own container.

Point `wyoming_openai` at:

```
OPENAI_URL = http://<docker-host>:7780/v1
```

…and add its Wyoming Protocol port to Home Assistant → Settings → Devices &
Services → Add Integration → **Wyoming Protocol**.

The `nadeko` voice from `voices.yaml` appears in the HA voice picker.

## Configuration

- `config/config.yaml` — server + backend URLs + auth
- `config/voices.yaml` — voice presets with reference clips and defaults

Both files ship with `.example` counterparts.

## License

MIT.
