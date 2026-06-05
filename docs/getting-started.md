# Getting Started

## Prerequisites

**Hardware**

- A microphone accessible to the OS (USB, 3.5 mm, or built-in).
- A speaker or headphone output for TTS playback.
- Enough compute to run STT and TTS models locally. A Raspberry Pi 4 (4 GB) is the practical minimum; Pi 5 or any x86 machine is comfortable.

**Software**

- Python 3.10 or later.
- A running [HiveMind-core](https://github.com/JarbasHiveMind/HiveMind-core) instance (the "hive") reachable from this device.

---

## Install

```bash
pip install HiveMind-voice-sat
```

**Linux** — adds ALSA and SoundDevice microphone backends:

```bash
pip install "HiveMind-voice-sat[linux]"
```

**macOS:**

```bash
pip install "HiveMind-voice-sat[mac]"
```

Default plugins installed alongside the core package:

| Role | Default plugin |
|------|---------------|
| VAD | `ovos-vad-plugin-silero` |
| Wakeword | `ovos-ww-plugin-vosk` |
| STT | `ovos-stt-plugin-server` |
| TTS | `ovos-tts-plugin-server` |

You can swap any of these — see [Configuration](configuration.md).

---

## Pairing: get an access key from the hive

On the machine running **HiveMind-core**, add a client entry and note the credentials it prints:

```bash
hivemind-core add-client --name my-voice-sat
```

Example output:

```
Access Key : abc123...
Password   : def456...
```

These two values identify this satellite to the hive. Keep them; they are not stored on the server after display (though you can re-list them with `hivemind-core list-clients`).

---

## First run

Pass the credentials and host directly on the command line:

```bash
hivemind-voice-sat \
  --host <hive-host-or-ip> \
  --key abc123... \
  --password def456... \
  --port 5678
```

Or store the identity once so you do not have to repeat flags:

```bash
hivemind-client set-identity \
  --host <hive-host-or-ip> \
  --key abc123... \
  --password def456...

hivemind-voice-sat   # reads ~/.config/mycroft/identity2.json
```

If neither credentials nor an identity file are present, the satellite falls back to **GGWave** — it listens for an audio-encoded identity broadcast from the hive (see `hivemind-ggwave`).

---

## Verify it works

1. Watch the log output. A successful connection prints:

   ```
   HiveMind Voice Satellite alive.
   HiveMind Voice Satellite is ready.
   ```

2. Say your wakeword (default: *Hey Mycroft*). You should hear a chime.
3. Ask a question: *"What time is it?"* The hive processes the utterance and the satellite speaks the response.

If you see connection errors, consult [Troubleshooting](troubleshooting.md).

---

## Next steps

- Swap STT/TTS/wakeword plugins: [Configuration](configuration.md)
- Run as a system service: [Deployment](deployment.md)
- Understand the data flow: [Architecture](architecture.md)
