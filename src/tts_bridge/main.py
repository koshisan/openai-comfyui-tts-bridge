"""FastAPI app entry point."""
from __future__ import annotations

import argparse
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .api import health as health_route
from .api import models as models_route
from .api import speech as speech_route
from .api import ui as ui_route
from .backends import ComfyUIBackend, PiperBackend
from .config import AppConfig, load_config
from .voices import VoiceRegistry, load_voices

log = logging.getLogger(__name__)


def build_backend(config: AppConfig):
    if config.default_backend == "comfyui":
        return ComfyUIBackend(config.comfyui)
    if config.default_backend == "piper":
        return PiperBackend(config.piper)
    raise ValueError(f"unknown default_backend: {config.default_backend}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    backend = app.state.backend
    log.info("using backend=%s", backend.name)
    yield
    if hasattr(backend, "close"):
        await backend.close()


def create_app(config: AppConfig | None = None, voices: VoiceRegistry | None = None) -> FastAPI:
    config = config or load_config()
    voices = voices or load_voices()
    app = FastAPI(title="openai-comfyui-tts-bridge", version="0.1.0", lifespan=lifespan)
    app.state.config = config
    app.state.voices = voices
    app.state.backend = build_backend(config)
    app.include_router(health_route.router)
    app.include_router(models_route.router)
    app.include_router(speech_route.router)
    app.include_router(ui_route.router)
    return app


def cli() -> None:
    parser = argparse.ArgumentParser(prog="tts-bridge")
    parser.add_argument("--config", help="path to config.yaml", default=None)
    parser.add_argument("--voices", help="path to voices.yaml", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    config = load_config(args.config)
    voices = load_voices(args.voices)
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port

    app = create_app(config, voices)
    uvicorn.run(app, host=config.server.host, port=config.server.port, log_level=args.log_level)


if __name__ == "__main__":
    cli()
