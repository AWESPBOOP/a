"""Rendering engine that feeds audio data into GPU shaders."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..recording.recorder import VideoRecorder

try:  # pragma: no cover - optional in headless CI
    import glfw
    import moderngl
except Exception:  # pragma: no cover
    glfw = None
    moderngl = None  # type: ignore

from ..audio.analysis import AudioAnalysisFrame
from .effects.shader_manager import ShaderManager
from .graph import EffectGraph

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class WindowConfig:
    width: int = 1280
    height: int = 720
    title: str = "NebulaVis"
    fullscreen: bool = False
    transparent: bool = False


@dataclass(slots=True)
class VisualEngineConfig:
    shader_dir: Path
    preset_path: Path
    window: WindowConfig = WindowConfig()
    swap_interval: int = 1


class VisualEngine:
    """Manage the OpenGL context and effect graph rendering."""

    def __init__(self, config: VisualEngineConfig) -> None:
        if moderngl is None or glfw is None:
            raise RuntimeError("Moderngl and GLFW are required for the visual engine")
        self._config = config
        self._shader_manager = ShaderManager(config.shader_dir)
        self._graph = EffectGraph.load(config.preset_path)
        self._preset_path = config.preset_path
        self._ctx: Optional[moderngl.Context] = None
        self._window: Optional[glfw._GLFWwindow] = None  # type: ignore[attr-defined]
        self._last_time = time.perf_counter()
        self._band_buffer: Optional[moderngl.Buffer] = None
        self._frame_uniform: Optional[moderngl.Buffer] = None
        self._quad_vbo: Optional[moderngl.Buffer] = None
        self._recorder: Optional[VideoRecorder] = None

    # ------------------------------------------------------------------
    def initialize(self) -> None:
        LOGGER.info("Initializing GLFW window")
        if not glfw.init():  # pragma: no cover - depends on system
            raise RuntimeError("Failed to initialize GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE if self._config.window.transparent else glfw.FALSE)
        monitor = glfw.get_primary_monitor() if self._config.window.fullscreen else None
        self._window = glfw.create_window(
            self._config.window.width,
            self._config.window.height,
            self._config.window.title,
            monitor,
            None,
        )
        if not self._window:
            raise RuntimeError("Failed to create GLFW window")
        glfw.make_context_current(self._window)
        glfw.swap_interval(self._config.swap_interval)
        self._ctx = moderngl.create_context()
        self._ctx.enable(moderngl.BLEND)
        self._ctx.blend_func = moderngl.BLEND_FUNC_ADD
        self._band_buffer = self._ctx.buffer(reserve=4 * 256)
        self._frame_uniform = self._ctx.buffer(reserve=4 * 16)
        self._band_buffer.bind_to_uniform_block(0)
        self._frame_uniform.bind_to_uniform_block(1)
        self._quad_vbo = self._ctx.buffer(self._fullscreen_quad())
        self._shader_manager.start()
        LOGGER.info("Visual engine initialized")

    def load_preset(self, path: Path) -> None:
        """Reload the effect graph from *path*."""

        self._graph = EffectGraph.load(path)
        self._preset_path = path
        LOGGER.info("Loaded preset %s", path)

    def load_graph(self, graph: EffectGraph) -> None:
        """Install an already constructed effect graph.""

        self._graph = graph


    def attach_recorder(self, recorder: Optional['VideoRecorder']) -> None:
        self._recorder = recorder

    def shutdown(self) -> None:
        LOGGER.info("Shutting down visual engine")
        self._shader_manager.stop()
        if self._quad_vbo:
            self._quad_vbo.release()
        if self._band_buffer:
            self._band_buffer.release()
        if self._frame_uniform:
            self._frame_uniform.release()
        if self._window:
            glfw.destroy_window(self._window)
        glfw.terminate()

    # ------------------------------------------------------------------
    def render_frame(self, frame: AudioAnalysisFrame) -> None:
        if self._ctx is None or self._window is None or self._quad_vbo is None:
            raise RuntimeError("Visual engine not initialized")
        now = time.perf_counter()
        delta = now - self._last_time
        self._last_time = now

        if self._band_buffer is not None:
            bands = frame.band_energies.astype("f4")
            if len(bands) < 256:
                bands = np.pad(bands, (0, 256 - len(bands)))
            self._band_buffer.write(bands.tobytes())
        if self._frame_uniform is not None:
            uniform = np.array(
                [
                    frame.tempo,
                    float(frame.beat),
                    frame.beat_phase,
                    frame.rms,
                    delta,
                    frame.spectral_centroid,
                    frame.spectral_rolloff,
                    frame.peak,
                ]
                + [0.0] * 8,
                dtype="f4",
            )
            self._frame_uniform.write(uniform.tobytes())

        self._ctx.clear(0.02, 0.02, 0.03, 1.0)
        width, height = glfw.get_framebuffer_size(self._window)
        self._ctx.viewport = (0, 0, width, height)

        for node in self._graph.enabled_nodes():
            program = self._load_program(node)
            if not program:
                continue
            if "BandData" in program:
                program["BandData"].binding = 0  # type: ignore[index]
            if "FrameData" in program:
                program["FrameData"].binding = 1  # type: ignore[index]
            if "uTime" in program:
                program["uTime"].value = now  # type: ignore[index]
            vao = self._ctx.simple_vertex_array(program, self._quad_vbo, "in_vert")
            vao.render(moderngl.TRIANGLE_STRIP)

        if self._recorder and self._recorder.is_recording:
            width, height = glfw.get_framebuffer_size(self._window)
            pixels = self._ctx.screen.read(components=4, dtype="f1")
            self._recorder.push_frame(pixels)
        glfw.swap_buffers(self._window)
        glfw.poll_events()

    def _fullscreen_quad(self) -> bytes:
        quad = np.array(
            [
                -1.0,
                -1.0,
                1.0,
                -1.0,
                -1.0,
                1.0,
                1.0,
                1.0,
            ],
            dtype="f4",
        )
        return quad.tobytes()

    def _load_program(self, node) -> Optional["moderngl.Program"]:
        shader = self._shader_manager.get(node.params.get("shader", node.type))
        try:
            program = self._ctx.program(vertex_shader=self._default_vertex_shader(), fragment_shader=shader.code)
        except Exception as exc:  # pragma: no cover - OpenGL runtime
            shader.last_error = str(exc)
            LOGGER.error("Shader compile error for %s: %s", shader.path, exc)
            return None
        shader.last_error = None
        return program

    def _default_vertex_shader(self) -> str:
        return """
        #version 330
        in vec2 in_vert;
        out vec2 v_uv;
        void main() {
            v_uv = in_vert * 0.5 + 0.5;
            gl_Position = vec4(in_vert, 0.0, 1.0);
        }
        """
