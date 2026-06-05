# HiveMind Voice Satellite — Documentation

HiveMind Voice Satellite (`hivemind-voice-sat`) is the **full-stack** OVOS satellite: every audio-processing stage runs on this device. The microphone is captured locally, VAD filters silence, a wakeword engine listens for your trigger phrase, STT converts speech to text, and that text is forwarded to the hive. Responses arrive as text and TTS speaks them locally. No raw audio ever leaves the device.

## Satellite spectrum

Understanding where each satellite sits on the local-vs-remote processing axis helps you pick the right tool:

| Satellite | Mic | VAD | Wakeword | STT | TTS | Wire payload |
|-----------|:---:|:---:|:--------:|:---:|:---:|--------------|
| [HiveMind-cli](https://github.com/JarbasHiveMind/HiveMind-cli) | — | — | — | — | — | text only |
| [hivemind-mic-satellite](https://github.com/JarbasHiveMind/hivemind-mic-satellite) | ✔ | ✔ | — | server | server | raw audio stream |
| [HiveMind-voice-relay](https://github.com/JarbasHiveMind/HiveMind-voice-relay) | ✔ | ✔ | ✔ | server | server | post-wakeword audio |
| **HiveMind-voice-sat** | ✔ | ✔ | ✔ | ✔ | ✔ | text utterances |

**When to choose voice-sat:**
- The device has enough CPU/GPU to run STT and TTS models locally (Raspberry Pi 4/5, x86, or any device with ≥2 GB RAM to spare).
- Bandwidth to the hive is limited or metered.
- Audio privacy is a requirement — no spoken audio leaves the device.
- You want the hive to remain lightweight and serve many clients.

**When to choose a thinner satellite:**
- The device is a minimal microcontroller or SBC with little compute.
- You want centralized STT/TTS model management on the server.

## Pages

| Page | Audience |
|------|----------|
| [Getting started](getting-started.md) | First-time setup, pairing, first run |
| [Configuration](configuration.md) | CLI flags, config file, plugin selection |
| [Architecture](architecture.md) | On-device pipeline, wire protocol, trade-offs |
| [Deployment](deployment.md) | systemd service, Raspberry Pi, audio hardware |
| [Troubleshooting](troubleshooting.md) | Common failure modes and fixes |
