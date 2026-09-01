# Deployment

## systemd service

Create `/etc/systemd/system/hivemind-voice-sat.service`:

```ini
[Unit]
Description=HiveMind Voice Satellite
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/pi/.venv/bin/hivemind-voice-sat \
    --host wss://your-hive-host:5678 \
    --key YOUR_ACCESS_KEY \
    --password YOUR_PASSWORD \
    --selfsigned
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Adjust `User` and the `hivemind-voice-sat` path to match your installation.
If you stored credentials in the identity file, drop `--key`, `--password`, and `--host`.

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hivemind-voice-sat
sudo journalctl -u hivemind-voice-sat -f
```

---

## Using the identity file instead of CLI flags

Storing credentials in the service unit exposes them in `systemctl status` output.
A cleaner approach is to populate the identity file once and omit the flags:

```bash
hivemind-client set-identity \
  --host wss://your-hive-host:5678 \
  --key YOUR_ACCESS_KEY \
  --password YOUR_PASSWORD
```

Then the `ExecStart` line simplifies to:

```ini
ExecStart=/home/pi/.venv/bin/hivemind-voice-sat
```

---

## Raspberry Pi notes

**Pi 4 (4 GB) minimum.** Pi 5 is comfortable with mid-size models.

### Audio group

The running user needs access to audio devices:

```bash
sudo usermod -aG audio pi
```

Log out and back in (or reboot) for the group change to take effect.

### Microphone selection

List devices:

```bash
arecord -l          # ALSA devices
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

Set the device in `~/.config/mycroft/mycroft.conf`:

```json
{
  "microphone": {
    "module": "ovos-microphone-plugin-alsa",
    "ovos-microphone-plugin-alsa": {
      "device_name": "hw:1,0"
    }
  }
}
```

Or with SoundDevice:

```json
{
  "microphone": {
    "module": "ovos-microphone-plugin-sounddevice",
    "ovos-microphone-plugin-sounddevice": {
      "device": 1
    }
  }
}
```

### Speaker selection

`ovos-audio` uses the system default ALSA/PulseAudio output. To override:

```bash
# check current default
aplay -l
# set default card in ~/.asoundrc
pcm.!default { type hw; card 1; }
ctl.!default { type hw; card 1; }
```

### Recommended local plugins for Pi

| Role | Plugin | Notes |
|------|--------|-------|
| VAD | `ovos-vad-plugin-silero` | Ships with voice-sat, fast on CPU |
| Wakeword | `ovos-ww-plugin-vosk` | Ships with voice-sat, small model |
| STT | `ovos-stt-plugin-faster-whisper` | `pip install ovos-stt-plugin-faster-whisper`, use `tiny` or `base` model on Pi 4 |
| TTS | `ovos-tts-plugin-piper` | `pip install ovos-tts-plugin-piper`, fast neural TTS, no GPU needed |

### Reduce latency on Pi

- Use a wired USB microphone rather than USB + sound card dongle.
- Prefer the `tiny` Whisper model for STT on Pi 4. Upgrade to `small` on Pi 5.
- Set `"continuous_listen": false` (default) so VAD + wakeword gate STT inference.

---

## Autostart without systemd (user session)

```bash
# ~/.config/autostart/hivemind-voice-sat.desktop
[Desktop Entry]
Type=Application
Name=HiveMind Voice Satellite
Exec=/home/pi/.venv/bin/hivemind-voice-sat
Hidden=false
X-GNOME-Autostart-enabled=true
```

---
[← Architecture](architecture.md) · [Home](index.md) · [Troubleshooting →](troubleshooting.md)
