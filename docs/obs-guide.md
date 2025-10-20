# OBS / Streaming Integration

NebulaVis can stream visuals to OBS using Spout (Windows) or Syphon (macOS). Linux users can capture the application window directly or via NDI.

## Spout (Windows)

1. Install the [Spout SDK](https://spout.zeal.co/).
2. Enable **Spout output** in the dashboard settings.
3. In OBS add a **Spout Capture** source and select *NebulaVis*.

## Syphon (macOS)

1. Install the [Syphon plugin for OBS](https://github.com/v002/v002-OBS-Syphon-Plugin).
2. Enable **Syphon output** in NebulaVis.
3. Add a **Syphon Client** source in OBS and choose *NebulaVis*.

## NDI (Optional)

Set `NEBULAVIS_ENABLE_NDI=1` before launching to expose an NDI sender. Use the OBS NDI plugin to receive the stream.

## Recording tips

- Use the built-in recorder (`R` hotkey) for precise frame pacing with ffmpeg.
- Match NebulaVis output resolution to your OBS canvas (e.g., 1920x1080 @ 60 FPS).
- Enable the performance HUD (`Ctrl+P`) to monitor frame time and audio buffer usage.
