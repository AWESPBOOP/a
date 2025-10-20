# NebulaVis

NebulaVis is a cross-platform, GPU-accelerated music visualizer written in Python. It couples low-latency audio analysis with a procedural shader graph engine capable of reacting to beats, spectral energy, and cloud metadata from Spotify or Apple Music.

## Features

- **Audio analysis** – FFT-based spectral features, beat and onset detection, tempo estimation, envelopes, and chroma vectors.
- **Capture modes** – Loopback capture via PortAudio (WASAPI, BlackHole, ALSA/Pulse) with microphone fallback.
- **Cloud metadata** – OAuth integrations with Spotify (currently playing, artwork, tempo) and Apple Music metadata.
- **Visual engine** – ModernGL renderer with hot-reloadable GLSL shaders, effect graph, bloom/post-fx nodes, and timeline cues.
- **Presets** – Ten showcase presets ranging from ambient nebulae to particle supernovas.
- **Recording & output** – Spout/Syphon bridge and ffmpeg-powered MP4 recording.
- **Extensibility** – Plugin API for adding shaders, modulators, or OSC controllers.

## Getting started

1. Install dependencies with [uv](https://github.com/astral-sh/uv):

   ```bash
   uv sync
   ```

2. Launch the visualizer:

   ```bash
   uv run nebulavis run --preset ambient_nebula
   ```

3. Open the Dear PyGui dashboard to choose the input device, authenticate Spotify/Apple Music, tweak presets, and monitor latency.

Comprehensive guides are available in the [`docs/`](docs/) directory.

## Testing

Run the automated tests with:

```bash
uv run pytest
```

## Building binaries

PyInstaller specs live in `packaging/specs/`. Use `uv run pyinstaller packaging/specs/nebulavis.spec` to produce a standalone build for your platform.

## License

MIT
