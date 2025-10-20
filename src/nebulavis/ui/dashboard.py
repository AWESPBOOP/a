"""Dear PyGui based control surface for NebulaVis."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

try:  # pragma: no cover - optional in tests
    from dearpygui import dearpygui as dpg
except Exception:  # pragma: no cover
    dpg = None  # type: ignore

from ..audio.pipeline import AudioPipeline
from ..integrations.spotify import SpotifyClient
from ..integrations.apple_music import AppleMusicClient
from ..visual.presets import PresetManager

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class DashboardCallbacks:
    on_latency_calibrate: Callable[[], None]
    on_preset_change: Callable[[str], None]
    on_record_toggle: Callable[[bool], None]


class Dashboard:
    """Small Dear PyGui wrapper to orchestrate the control UI."""

    def __init__(
        self,
        pipeline: AudioPipeline,
        preset_manager: PresetManager,
        spotify: Optional[SpotifyClient],
        apple_music: Optional[AppleMusicClient],
        callbacks: DashboardCallbacks,
    ) -> None:
        if dpg is None:
            raise RuntimeError("Dear PyGui is required for the dashboard")
        self._pipeline = pipeline
        self._preset_manager = preset_manager
        self._spotify = spotify
        self._apple_music = apple_music
        self._callbacks = callbacks
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="NebulaVisUI", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._thread:
            return
        self._stop.set()
        if dpg.is_dearpygui_running():
            dpg.stop_dearpygui()
        self._thread.join(timeout=2.0)
        self._thread = None

    # ------------------------------------------------------------------
    def _run(self) -> None:
        dpg.create_context()
        self._build_ui()
        dpg.create_viewport(title="NebulaVis", width=420, height=720)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        while dpg.is_dearpygui_running() and not self._stop.is_set():
            self._update_now_playing()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()

    def _build_ui(self) -> None:
        with dpg.window(label="NebulaVis", tag="root", width=420, height=720):
            dpg.add_text("Audio Capture")
            devices = [device["name"] for device in self._pipeline.capture.list_devices()]
            dpg.add_combo(devices, label="Input Device", callback=self._on_device_change)
            dpg.add_button(label="Latency Wizard", callback=lambda: self._callbacks.on_latency_calibrate())
            dpg.add_separator()
            dpg.add_text("Cloud Sync")
            if self._spotify:
                dpg.add_button(label="Login Spotify", callback=lambda: self._login_async(self._spotify.authenticate))
            if self._apple_music:
                dpg.add_button(label="Login Apple Music", callback=lambda: self._login_async(self._apple_music.authenticate))
            dpg.add_separator()
            dpg.add_text("Presets")
            dpg.add_listbox([], tag="preset_list", callback=self._on_preset_selected)
            dpg.add_button(label="Refresh Presets", callback=self._refresh_presets)
            dpg.add_separator()
            dpg.add_checkbox(label="Record", callback=self._on_record_toggle)
            dpg.add_progress_bar(tag="latency_bar", overlay="Latency")
            dpg.add_text("Now Playing", tag="now_playing")
            with dpg.group(horizontal=True):
                dpg.add_text("BPM:")
                dpg.add_text("--", tag="bpm_label")
        self._refresh_presets()

    def _on_device_change(self, sender, app_data, user_data=None):  # pragma: no cover - GUI callback
        LOGGER.info("Device changed: %s", app_data)

    def _on_preset_selected(self, sender, app_data, user_data=None):  # pragma: no cover - GUI callback
        self._callbacks.on_preset_change(app_data)

    def _on_record_toggle(self, sender, app_data, user_data=None):  # pragma: no cover - GUI callback
        self._callbacks.on_record_toggle(bool(app_data))

    def _login_async(self, func: Callable[[], None]) -> None:
        threading.Thread(target=func, daemon=True).start()

    def _refresh_presets(self) -> None:
        presets = self._preset_manager.list_presets()
        dpg.configure_item("preset_list", items=presets)

    def _update_now_playing(self) -> None:
        if self._spotify and self._spotify.state.now_playing:
            track = self._spotify.state.now_playing
            overlay = f"{track.artist} — {track.title}"
            dpg.set_value("now_playing", overlay)
            dpg.set_value("bpm_label", f"{track.tempo:.1f}" if track.tempo else "--")
        latency_ms = self._pipeline.latency_budget()
        dpg.set_value("latency_bar", min(latency_ms / 100.0, 1.0))
        dpg.set_item_label("latency_bar", f"Latency: {latency_ms:.1f} ms")
