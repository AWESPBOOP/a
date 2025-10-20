# Audio Device Setup

NebulaVis analyzes audio using loopback capture or microphone input. The lowest latency experience comes from routing the system playback mix into an input device.

## Windows (WASAPI loopback)

1. Right-click the speaker icon and open **Sound settings**.
2. Under **Related settings** select **More sound settings**.
3. In the **Recording** tab, enable the **Stereo Mix** or your device's loopback input. If unavailable, install [VB-Cable](https://vb-audio.com/Cable/) and select its input.
4. In NebulaVis choose the device labelled *loopback* from the dashboard combo box.

## macOS (BlackHole)

1. Install [BlackHole](https://existential.audio/blackhole/) 2-channel.
2. Open **Audio MIDI Setup**, create a **Multi-Output Device** combining your speakers/headphones and BlackHole.
3. Set the multi-output device as the system output.
4. In NebulaVis select **BlackHole 2ch** as the input device.

## Linux (PulseAudio / PipeWire)

- **PulseAudio**: In `pavucontrol` enable the *Monitor of Built-in Audio Analog Stereo* input.
- **PipeWire**: Use `pw-loopback` or `helvum` to connect the desired playback stream to a loopback node.

If loopback devices are unavailable, choose any microphone input. Use the latency calibration wizard to offset microphone delay.
