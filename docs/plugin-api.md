# Plugin API

NebulaVis exposes a lightweight plugin interface for adding shaders, modulators, or control surfaces.

## Manifest

Create a folder with a `plugins.json` manifest:

```json
{
  "plugins": [
    {
      "name": "My Plugin",
      "module": "my_plugin.entry",
      "entry": "register"
    }
  ]
}
```

Point the `PluginManager` at the folder. Each plugin module must define a callable `register()` function.

## Shader plugins

In `register()` you can install additional shaders or presets by writing to the plugin folder. The example plugin (`examples/plugins/example_plugin.py`) generates a shader file and preset on import.

## Custom modulators

Plugins can subscribe to audio frames by importing `nebulavis.audio.pipeline.AudioPipeline` and attaching callbacks. The pipeline exposes `AudioPipeline.frames()` which yields `AudioAnalysisFrame` objects.

## Remote control

Expose OSC or WebSocket endpoints in your plugin. Use `pip install python-osc` within your virtual environment and bind incoming messages to `PresetManager.update_param()` for real-time control.

## Packaging

Distribute plugins as zip archives containing the manifest, shader files, and Python modules. End users drop the folder into `~/Documents/NebulaVis/plugins` and enable it from the dashboard.
