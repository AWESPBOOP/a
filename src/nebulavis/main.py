"""NebulaVis entry point."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from .audio.pipeline import AudioPipeline, AudioPipelineConfig
from .audio.latency import LatencyCalibrator
from .integrations.apple_music import AppleMusicClient, AppleMusicTokens
from .integrations.spotify import SpotifyClient, TokenStore
from .recording.recorder import RecorderConfig, VideoRecorder
from .ui.dashboard import Dashboard, DashboardCallbacks
from .utils.logging import configure_logging
from .visual.engine import VisualEngine, VisualEngineConfig
from .visual.presets import PresetManager

app = typer.Typer(add_completion=False)


async def _run_engine(pipeline: AudioPipeline, engine: VisualEngine) -> None:
    pipeline.start()
    engine.initialize()
    try:
        async for frame in pipeline.frames():
            engine.render_frame(frame)
    finally:
        engine.shutdown()
        pipeline.stop()


@app.command()
def run(
    shader_dir: Path = typer.Option(Path("src/nebulavis/resources/shaders"), help="Directory containing GLSL shaders"),
    preset: str = typer.Option("ambient_nebula", help="Preset name to load"),
    preset_dir: Path = typer.Option(Path("src/nebulavis/resources/presets"), help="Preset directory"),
    spotify_client_id: Optional[str] = typer.Option(None, envvar="NEBULAVIS_SPOTIFY_CLIENT_ID"),
    apple_developer_token: Optional[str] = typer.Option(None, envvar="NEBULAVIS_APPLE_DEVELOPER_TOKEN"),
    log_level: str = typer.Option("INFO", help="Logging level"),
) -> None:
    """Start the NebulaVis realtime visualizer."""

    configure_logging(getattr(logging, log_level.upper(), logging.INFO))
    preset_manager = PresetManager(preset_dir)
    if preset not in preset_manager.list_presets():
        raise typer.BadParameter(f"Preset {preset} not found in {preset_dir}")
    audio_config = AudioPipelineConfig()
    pipeline = AudioPipeline(audio_config)

    preset_path = preset_dir / f"{preset}.json"
    engine_config = VisualEngineConfig(shader_dir=shader_dir, preset_path=preset_path)
    engine = VisualEngine(engine_config)

    spotify_client = SpotifyClient(spotify_client_id, TokenStore(Path.home() / ".config/nebulavis/spotify.json")) if spotify_client_id else None
    apple_client = AppleMusicClient(AppleMusicTokens(apple_developer_token), Path.home() / ".config/nebulavis/apple_music.json") if apple_developer_token else None

    recorder: Optional[VideoRecorder] = None

    def on_latency_calibrate() -> None:
        logging.info("Latency calibration requested from UI")

    def on_preset_change(name: str) -> None:
        try:
            engine.load_preset(preset_dir / f"{name}.json")
        except FileNotFoundError:
            logging.error("Preset %s not found", name)

    def on_record_toggle(active: bool) -> None:
        nonlocal recorder
        if active:
            output_dir = Path.home() / "Videos" / "NebulaVis"
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = output_dir / f"nebula_{datetime.now():%Y%m%d-%H%M%S}.mp4"
            recorder = VideoRecorder(RecorderConfig(output_path=filename))
            recorder.start()
            engine.attach_recorder(recorder)
            logging.info("Recording to %s", filename)
        else:
            if recorder:
                recorder.stop()
                engine.attach_recorder(None)
                recorder = None
                logging.info("Recording stopped")

    callbacks = DashboardCallbacks(
        on_latency_calibrate=on_latency_calibrate,
        on_preset_change=on_preset_change,
        on_record_toggle=on_record_toggle,
    )
    dashboard = Dashboard(pipeline, preset_manager, spotify_client, apple_client, callbacks)
    dashboard.start()
    try:
        asyncio.run(_run_engine(pipeline, engine))
    finally:
        dashboard.stop()
        if recorder:
            recorder.stop()



@app.command()
def calibrate(
    reference: Path = typer.Argument(..., help="Reference audio recording"),
    captured: Path = typer.Argument(..., help="Captured loopback recording"),
    samplerate: int = typer.Option(48000, help="Samplerate of the recordings"),
) -> None:
    """Estimate latency offset between reference and captured audio."""

    import soundfile as sf  # type: ignore

    ref_data, _ = sf.read(reference)
    cap_data, _ = sf.read(captured)
    calibrator = LatencyCalibrator(samplerate)
    result = calibrator.calibrate(ref_data, cap_data)
    typer.echo(f"Latency offset: {result.offset_ms:.2f} ms (correlation {result.correlation:.2f})")


def app_entry() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    app_entry()
