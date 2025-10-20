# Shader Authoring Guide

NebulaVis ships with a hot-reloadable shader pipeline powered by ModernGL. Shaders live in `src/nebulavis/resources/shaders` or any folder watched by the Shader Manager.

## Uniforms

Each fragment shader receives the following data:

```glsl
layout(std140) uniform BandData { float bands[256]; };
layout(std140) uniform FrameData { float frame[16]; };
uniform float uTime;
```

- `bands`: normalized energy per frequency band (0 = silence, 1 = peak). Index ranges 0-255.
- `frame[0]`: tempo (BPM)
- `frame[1]`: beat flag (1.0 on beat detection)
- `frame[2]`: beat phase (0-1)
- `frame[3]`: RMS level
- `frame[4]`: frame delta time
- `frame[5]`: spectral centroid
- `frame[6]`: spectral rolloff
- `frame[7]`: peak amplitude

Additional slots are reserved for future modulators (timeline cues, palette indices).

## File structure

- Vertex shader: NebulaVis supplies a default fullscreen quad vertex shader.
- Fragment shader: Provide your effect implementation in GLSL 330.

## Hot reload

The `ShaderManager` watches the shader directory. Saving a file triggers recompilation; errors are logged in the dashboard console and the previous successful shader remains active.

## Debugging tips

- Use `uTime` to animate and `bands` to react to audio.
- Multiply band values by modulators such as `frame[1]` (beat) for punchy pulses.
- Keep calculations branch-free for performance; prefer `mix`, `smoothstep`, and vector operations.
- Profile GPU time with the performance HUD (Ctrl+P).
