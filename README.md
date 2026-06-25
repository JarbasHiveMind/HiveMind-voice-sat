[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/JarbasHiveMind/HiveMind-voice-sat)

# HiveMind Voice Satellite

The **full-stack** OVOS voice satellite: microphone, VAD, wakeword, STT, and TTS all run **on this device**. Spoken input is transcribed locally; only the resulting text utterance is sent to the hive. Responses arrive as text and are spoken locally. Requires the most compute of the satellite family, but puts the least load on the server and works fully offline once set up.

## Satellite spectrum

| Satellite | Mic | VAD | Wakeword | STT | TTS | What crosses the wire |
|-----------|:---:|:---:|:--------:|:---:|:---:|-----------------------|
| [HiveMind-cli](https://github.com/JarbasHiveMind/HiveMind-cli) | — | — | — | — | — | text in / text out |
| [hivemind-mic-satellite](https://github.com/JarbasHiveMind/hivemind-mic-satellite) | local | local | — | **remote** | **remote** | raw audio stream |
| [HiveMind-voice-relay](https://github.com/JarbasHiveMind/HiveMind-voice-relay) | local | local | local | **remote** | **remote** | audio after wakeword |
| **HiveMind-voice-sat** ← you are here | local | local | local | **local** | **local** | text utterances only |

Use voice-sat when the device has CPU/GPU to spare, when bandwidth is limited, or when audio privacy matters.

## Install

```bash
pip install HiveMind-voice-sat
# Linux — ALSA/SoundDevice microphone support
pip install HiveMind-voice-sat[linux]
# macOS
pip install HiveMind-voice-sat[mac]
```

## 60-second quickstart

**1. Add a client on the hive** (run this on the server):

```bash
hivemind-core add-client --name my-voice-sat
# outputs: Access Key and Password — copy them
```

**2. Run the satellite** (on this device):

```bash
hivemind-voice-sat --host <hive-host> --key <access-key> --password <password>
```

Say your wakeword; the satellite transcribes locally and sends the utterance to the hive.

## Minimal configuration

The satellite reads `~/.config/mycroft/mycroft.conf` (standard OVOS config).
Override STT, TTS, VAD, and wakeword plugins there:

```json
{
  "listener": {
    "VAD": {
      "module": "ovos-vad-plugin-silero"
    },
    "wake_word": "hey_mycroft",
    "hey_mycroft": {
      "module": "ovos-ww-plugin-vosk"
    }
  },
  "stt": {
    "module": "ovos-stt-plugin-server",
    "ovos-stt-plugin-server": { "url": "https://stt.openvoiceos.org/stt" }
  },
  "tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": { "host": "https://tts.openvoiceos.org" }
  }
}
```

All plugin slots are swappable via [ovos-plugin-manager](https://github.com/OpenVoiceOS/ovos-plugin-manager). See [docs/configuration.md](docs/configuration.md) for the full reference.

## CLI reference

```
Usage: hivemind-voice-sat [OPTIONS]

  connect to HiveMind

Options:
  --host TEXT       hivemind host (ws:// or wss://)
  --key TEXT        Access Key
  --password TEXT   Password for key derivation
  --port INTEGER    HiveMind port number (default 5678)
  --selfsigned      accept self-signed certificates
  --siteid TEXT     location identifier for message.context
  --help            Show this message and exit.
```

## Documentation

Full zero-to-hero docs live in **[docs/](docs/index.md)**:

- [Overview & architecture spectrum](docs/index.md)
- [Getting started](docs/getting-started.md)
- [Configuration reference](docs/configuration.md)
- [Architecture (advanced)](docs/architecture.md)
- [Deployment (systemd / Raspberry Pi)](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Testing & development](docs/testing.md)

## Development

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-voice-sat
cd HiveMind-voice-sat
pip install -e ".[test]"   # lightweight smoke deps
pytest tests/test_smoke.py
pip install -e ".[e2e]"    # full hivemind-core + 2.x stack for end-to-end
pytest tests/e2e/
```

`pyproject.toml` is the single packaging source of truth. The dependency stack
now runs on `ovos-bus-client` **2.x** (see [docs/architecture.md](docs/architecture.md#dependency-stack-the-bus-client-2x-situation));
prerelease deps are pinned as minimum versions so `pip` resolves them without `--pre`.

## Related

| Project | Role |
|---------|------|
| [HiveMind-core](https://github.com/JarbasHiveMind/HiveMind-core) | The hive — install on the server |
| [HiveMind-cli](https://github.com/JarbasHiveMind/HiveMind-cli) | Text-only client |
| [hivemind-mic-satellite](https://github.com/JarbasHiveMind/hivemind-mic-satellite) | Thinnest audio satellite |
| [HiveMind-voice-relay](https://github.com/JarbasHiveMind/HiveMind-voice-relay) | Mid-weight: local wakeword, remote STT/TTS |

## License

Apache-2.0 — see [LICENSE](LICENSE).
