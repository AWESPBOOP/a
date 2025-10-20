"""Shader hot-reload manager."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ShaderSource:
    path: Path
    code: str
    last_error: str | None = None


class ShaderFileHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[Path], None]) -> None:
        super().__init__()
        self._on_change = on_change

    def on_modified(self, event):  # type: ignore[override]
        if not event.is_directory:
            self._on_change(Path(event.src_path))

    def on_created(self, event):  # type: ignore[override]
        if not event.is_directory:
            self._on_change(Path(event.src_path))


class ShaderManager:
    """Load and hot-reload shader files from a directory."""

    def __init__(self, shader_dir: Path) -> None:
        self._shader_dir = shader_dir
        self._shaders: Dict[str, ShaderSource] = {}
        self._observer: Optional[Observer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._observer:
            return
        self._observer = Observer()
        handler = ShaderFileHandler(self._handle_change)
        self._observer.schedule(handler, str(self._shader_dir), recursive=False)
        self._observer.daemon = True
        self._observer.start()
        LOGGER.info("Started shader watcher for %s", self._shader_dir)

    def stop(self) -> None:
        if not self._observer:
            return
        self._observer.stop()
        self._observer.join(timeout=1.5)
        self._observer = None

    def list(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self._shaders.keys())

    def get(self, name: str) -> ShaderSource:
        self._ensure_loaded()
        return self._shaders[name]

    def _ensure_loaded(self) -> None:
        if self._shaders:
            return
        for file in self._shader_dir.glob("*.glsl"):
            self._load_shader(file)

    def _load_shader(self, path: Path) -> None:
        try:
            code = path.read_text()
        except FileNotFoundError:
            LOGGER.error("Shader %s not found", path)
            return
        shader = ShaderSource(path=path, code=code)
        self._shaders[path.stem] = shader
        LOGGER.debug("Loaded shader %s", path.stem)

    def _handle_change(self, path: Path) -> None:
        with self._lock:
            self._load_shader(path)
            LOGGER.info("Reloaded shader %s", path.stem)
