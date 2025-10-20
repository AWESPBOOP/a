"""Preset loading and saving for NebulaVis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .graph import EffectGraph

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class Preset:
    name: str
    path: Path


class PresetManager:
    def __init__(self, preset_dir: Path) -> None:
        self._preset_dir = preset_dir
        self._preset_dir.mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> list[str]:
        return sorted(p.stem for p in self._preset_dir.glob("*.json"))

    def load(self, name: str) -> EffectGraph:
        path = self._preset_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"Preset {name} not found")
        return EffectGraph.load(path)

    def save(self, name: str, graph: EffectGraph) -> Path:
        path = self._preset_dir / f"{name}.json"
        graph.save(path)
        return path

    def ensure_default_presets(self, defaults: dict[str, dict]) -> None:
        for name, payload in defaults.items():
            path = self._preset_dir / f"{name}.json"
            if not path.exists():
                path.write_text(json.dumps(payload, indent=2))
                LOGGER.info("Installed default preset %s", name)
