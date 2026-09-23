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

The compose file starts two containers on the same network:

- `tts-bridge` on port **7780** — the OpenAI-compatible HTTP API and web UI.
- `wyoming_openai` on port **10300** — a Wyoming Protocol server (from
  [roryeckel/wyoming_openai](https://github.com/roryeckel/wyoming_openai))
  that translates Wyoming requests into calls against `tts-bridge`.

In Home Assistant → Settings → Devices & Services → Add Integration →
**Wyoming Protocol**, enter:

- Host: the docker host that runs this stack (e.g. `192.168.1.10`)
- Port: `10300`

The bridge is now HA's TTS backend. The `nadeko` voice from `voices.yaml`
appears in the voice picker.

## Configuration

- `config/config.yaml` — server + backend URLs + auth
- `config/voices.yaml` — voice presets with reference clips and defaults

Both files ship with `.example` counterparts.

## License

MIT.
