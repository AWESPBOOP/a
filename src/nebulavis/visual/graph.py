"""Node graph representation for NebulaVis visual effects."""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class GraphInput:
    name: str
    source: str
    scale: float = 1.0
    bias: float = 0.0


@dataclass(slots=True)
class GraphNode:
    """An individual effect node in the graph."""

    identifier: str
    type: str
    inputs: list[GraphInput] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass(slots=True)
class EffectGraph:
    """Collection of effect nodes describing the render pipeline."""

    nodes: list[GraphNode] = field(default_factory=list)
    composites: list[dict[str, Any]] = field(default_factory=list)
    active_camera: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EffectGraph":
        nodes = [
            GraphNode(
                identifier=node["identifier"],
                type=node["type"],
                inputs=[GraphInput(**inp) for inp in node.get("inputs", [])],
                params=dict(node.get("params", {})),
                enabled=bool(node.get("enabled", True)),
            )
            for node in payload.get("nodes", [])
        ]
        composites = list(payload.get("composites", []))
        active_camera = payload.get("active_camera")
        return cls(nodes=nodes, composites=composites, active_camera=active_camera)

    @classmethod
    def load(cls, path: Path) -> "EffectGraph":
        LOGGER.debug("Loading effect graph from %s", path)
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))

    def node_by_id(self, identifier: str) -> Optional[GraphNode]:
        for node in self.nodes:
            if node.identifier == identifier:
                return node
        return None

    def update_param(self, node_id: str, key: str, value: Any) -> None:
        node = self.node_by_id(node_id)
        if not node:
            raise KeyError(f"Node {node_id!r} not found")
        node.params[key] = value
        LOGGER.debug("Updated node %s param %s=%s", node_id, key, value)

    def enabled_nodes(self) -> Iterable[GraphNode]:
        return (node for node in self.nodes if node.enabled)

    def merge(self, other: "EffectGraph") -> None:
        existing_ids = {node.identifier for node in self.nodes}
        for node in other.nodes:
            if node.identifier in existing_ids:
                LOGGER.warning("Duplicate node id %s encountered during merge", node.identifier)
                continue
            self.nodes.append(node)
        self.composites.extend(other.composites)
        if other.active_camera:
            self.active_camera = other.active_camera


class GraphValidator:
    """Validate a graph against supported node and input definitions."""

    def __init__(self, node_types: Mapping[str, Mapping[str, Any]]) -> None:
        self._node_types = node_types

    def validate(self, graph: EffectGraph) -> list[str]:
        errors: list[str] = []
        for node in graph.nodes:
            if node.type not in self._node_types:
                errors.append(f"Unsupported node type: {node.type}")
                continue
            spec = self._node_types[node.type]
            for inp in node.inputs:
                if inp.name not in spec.get("inputs", {}):
                    errors.append(f"Node {node.identifier}: unknown input {inp.name}")
        return errors
