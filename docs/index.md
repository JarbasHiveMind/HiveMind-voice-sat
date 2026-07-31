# HiveMind Voice Satellite Documentation

HiveMind Voice Satellite (`hivemind-voice-sat`) is a full-stack OVOS satellite. Every audio-processing stage runs on this device. The satellite captures the microphone locally, VAD filters silence, a wakeword engine listens for the trigger phrase, STT converts speech to text, and the satellite forwards that text to the hive. Responses arrive as text and TTS speaks them locally. No raw audio leaves the device.

## Satellite spectrum

This table shows where each satellite sits on the local-vs-remote processing axis.

| Satellite | Mic | VAD | Wakeword | STT | TTS | Wire payload |
|-----------|:---:|:---:|:--------:|:---:|:---:|--------------|
| [HiveMind-cli](https://github.com/JarbasHiveMind/HiveMind-cli) | n/a | n/a | n/a | n/a | n/a | text only |
| [hivemind-mic-satellite](https://github.com/JarbasHiveMind/hivemind-mic-satellite) | yes | yes | n/a | server | server | raw audio stream |
| [HiveMind-voice-relay](https://github.com/JarbasHiveMind/HiveMind-voice-relay) | yes | yes | yes | server | server | post-wakeword audio |
| **HiveMind-voice-sat** | yes | yes | yes | yes | yes | text utterances |

**When to choose voice-sat:**
- The device has enough CPU/GPU to run STT and TTS models locally (Raspberry Pi 4/5, x86, or any device with ≥2 GB RAM to spare).
- Bandwidth to the hive is limited or metered.
- Audio privacy is a requirement. No spoken audio leaves the device.
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
| [Testing](testing.md) | Test tiers, the bus-client 2.x stack, running e2e |
