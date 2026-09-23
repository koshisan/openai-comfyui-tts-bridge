# Multi-stage build for openai-comfyui-tts-bridge.
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip build \
    && pip wheel --no-deps --wheel-dir /wheels .


FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
COPY pyproject.toml ./
RUN pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels

# Config lives at /etc/tts-bridge/, override via bind mount.
ENV TTS_BRIDGE_CONFIG=/etc/tts-bridge/config.yaml \
    TTS_BRIDGE_VOICES=/etc/tts-bridge/voices.yaml

EXPOSE 7780
CMD ["tts-bridge"]
