from __future__ import annotations

from pathlib import Path

from nebulavis.visual.presets import PresetManager


def test_default_presets_exist(tmp_path: Path):
    preset_dir = Path('src/nebulavis/resources/presets')
    manager = PresetManager(preset_dir)
    presets = manager.list_presets()
    assert len(presets) >= 10
    graph = manager.load('ambient_nebula')
    assert graph.nodes
    assert graph.nodes[0].params['shader'] == 'ambient_nebula'
