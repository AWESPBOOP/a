"""Output bridges for NebulaVis rendering."""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SpoutConfig:
    enabled: bool = False
    sender_name: str = "NebulaVis"


@dataclass(slots=True)
class SyphonConfig:
    enabled: bool = False
    server_name: str = "NebulaVis"


class SpoutSender:
    """Thin wrapper around Spout for Windows."""

    def __init__(self, config: SpoutConfig) -> None:
        self._config = config
        self._sender = None

    def initialize(self) -> None:
        if not self._config.enabled:
            return
        try:  # pragma: no cover - optional dependency
            from spout import SpoutSender as _SpoutSender  # type: ignore
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Spout unavailable: %s", exc)
            return
        self._sender = _SpoutSender()
        self._sender.create_sender(self._config.sender_name, 0, 0)
        LOGGER.info("Spout sender ready: %s", self._config.sender_name)

    def send_texture(self, texture_id: int, width: int, height: int) -> None:
        if not self._sender:
            return
        self._sender.send_texture(texture_id, width, height, False)

    def shutdown(self) -> None:
        if self._sender:
            with contextlib.suppress(Exception):  # pragma: no cover
                self._sender.release()
        self._sender = None


class SyphonServer:
    """Minimal Syphon server wrapper for macOS."""

    def __init__(self, config: SyphonConfig) -> None:
        self._config = config
        self._server = None

    def initialize(self) -> None:
        if not self._config.enabled:
            return
        try:  # pragma: no cover
            from syphon import SyphonServer as _SyphonServer  # type: ignore
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Syphon unavailable: %s", exc)
            return
        self._server = _SyphonServer(server_name=self._config.server_name)
        LOGGER.info("Syphon server ready: %s", self._config.server_name)

    def publish_texture(self, texture_id: int, width: int, height: int) -> None:
        if not self._server:
            return
        self._server.publish_frame_texture(texture_id, width, height)

    def shutdown(self) -> None:
        if self._server:
            with contextlib.suppress(Exception):  # pragma: no cover
                self._server.stop()
        self._server = None
