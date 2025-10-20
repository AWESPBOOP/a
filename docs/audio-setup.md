# Audio Device Setup

NebulaVis analyzes audio using loopback capture or microphone input. The lowest latency experience comes from routing the system playback mix into an input device.

## Windows (WASAPI loopback)

### Option A – enable Stereo Mix (most laptops/desktops)

1. **Open the sound control panel**
   - Right-click the speaker icon in the taskbar and choose **Sound settings**.
   - Scroll down to **Related settings** and click **More sound settings** to open the legacy dialog.
2. **Show disabled devices**
   - In the **Recording** tab, right-click anywhere in the device list.
   - Check both **Show Disabled Devices** and **Show Disconnected Devices**.
3. **Enable loopback input**
   - Right-click **Stereo Mix** (or a similarly named *What U Hear* / *Loopback* device) and choose **Enable**.
   - Set it as the **Default Device** if you plan to use it regularly.
4. **Select it inside NebulaVis**
   - Launch NebulaVis, open the dashboard, and pick the device labelled *Stereo Mix* (or equivalent) from the input selector.

### Option B – install VB-Cable (when Stereo Mix is unavailable)

1. Download the latest VB-Cable ZIP from [vb-audio.com/Cable](https://vb-audio.com/Cable/).
2. Extract the archive, right-click `VBCABLE_Setup_x64.exe` (or `VBCABLE_Setup.exe` on 32-bit Windows), and choose **Run as administrator**.
3. Click **Install Driver**. Reboot Windows when prompted so the virtual cable appears.
4. Back in the **Recording** tab, rename the new **CABLE Output** device to something recognizable (optional but helpful).
5. In Windows **Sound settings** set your default playback device to **CABLE Input**. You can create a *Listen to this device* passthrough to your speakers if needed.
6. In NebulaVis, choose **CABLE Output** as the audio input device.

Once loopback is configured, play any audio source and verify that the NebulaVis spectrum responds immediately. If you still prefer a microphone feed, select it and run the latency calibration wizard to align the visuals.

## macOS (BlackHole)

1. Install [BlackHole](https://existential.audio/blackhole/) 2-channel.
2. Open **Audio MIDI Setup**, create a **Multi-Output Device** combining your speakers/headphones and BlackHole.
3. Set the multi-output device as the system output.
4. In NebulaVis select **BlackHole 2ch** as the input device.

## Linux (PulseAudio / PipeWire)

- **PulseAudio**: In `pavucontrol` enable the *Monitor of Built-in Audio Analog Stereo* input.
- **PipeWire**: Use `pw-loopback` or `helvum` to connect the desired playback stream to a loopback node.

If loopback devices are unavailable, choose any microphone input. Use the latency calibration wizard to offset microphone delay.
