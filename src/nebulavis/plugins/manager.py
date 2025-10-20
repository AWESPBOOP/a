"""Plugin system for NebulaVis."""

from __future__ import annotations

import importlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterable

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PluginDescriptor:
    name: str
    module: str
    entry: str


class PluginManager:
    def __init__(self, search_paths: Iterable[Path]) -> None:
        self._search_paths = list(search_paths)
        self._plugins: Dict[str, ModuleType] = {}

    def discover(self) -> list[PluginDescriptor]:
        descriptors: list[PluginDescriptor] = []
        for path in self._search_paths:
            manifest = path / "plugins.json"
            if not manifest.exists():
                continue
            data = json.loads(manifest.read_text())
            for entry in data.get("plugins", []):
                descriptors.append(PluginDescriptor(**entry))
        return descriptors

    def load(self, descriptor: PluginDescriptor) -> ModuleType:
        if descriptor.module in self._plugins:
            return self._plugins[descriptor.module]
        if descriptor.module not in sys.modules:
            module = importlib.import_module(descriptor.module)
        else:
            module = sys.modules[descriptor.module]
        if not hasattr(module, descriptor.entry):
            raise AttributeError(f"Plugin {descriptor.module} missing entry {descriptor.entry}")
        getattr(module, descriptor.entry)()
        self._plugins[descriptor.module] = module
        LOGGER.info("Loaded plugin %s", descriptor.name)
        return module
