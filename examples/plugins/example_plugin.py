"""Example NebulaVis plugin adding a shader and OSC bridge."""

from __future__ import annotations

import json
import logging
from pathlib import Path
LOGGER = logging.getLogger(__name__)


def register() -> None:
    LOGGER.info("Registering example plugin")
    shader_dir = Path(__file__).resolve().parent / "shaders"
    shader_dir.mkdir(exist_ok=True)
    shader_path = shader_dir / "example_wave.glsl"
    shader_path.write_text(
        """
        #version 330
        layout(std140) uniform BandData { float bands[256]; };
        uniform float uTime;
        out vec4 fragColor;
        void main() {
            vec2 uv = gl_FragCoord.xy / vec2(1920.0, 1080.0) - 0.5;
            float wave = sin(uv.x * 12.0 + uTime * 2.0) * 0.5 + 0.5;
            float band = bands[int(mod(gl_FragCoord.x, 128.0))];
            vec3 color = vec3(wave * band, 0.4 + band, 0.8 - wave * 0.2);
            fragColor = vec4(color, 1.0);
        }
        """.strip()
    )
    preset_dir = Path(__file__).resolve().parent / "presets"
    preset_dir.mkdir(exist_ok=True)
    preset_dir.joinpath("example_wave.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "identifier": "example",
                        "type": "shader",
                        "inputs": [
                            {"name": "bands", "source": "audio.bands", "scale": 1.0, "bias": 0.0}
                        ],
                        "params": {"shader": "example_wave"},
                    }
                ],
                "composites": [],
            },
            indent=2,
        )
    )
