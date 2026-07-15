# Configuration

## CLI flags

All flags are optional; missing values fall back to the stored identity (see below).

```
Usage: hivemind-voice-sat [OPTIONS]

  connect to HiveMind

Options:
  --host TEXT       HiveMind host. Include protocol: ws://host or wss://host.
                    If bare hostname is given, ws:// is assumed.
  --key TEXT        Access Key issued by hivemind-core add-client.
  --password TEXT   Password for key derivation.
  --port INTEGER    HiveMind WebSocket port. Default: 5678.
  --selfsigned      Accept self-signed TLS certificates (wss:// targets).
  --siteid TEXT     Location tag written into message.context. Useful when
                    multiple satellites share one hive.
  --help            Show this message and exit.
```

---

## Identity file

When `--host`, `--key`, and `--password` are all omitted, the satellite reads
`~/.config/mycroft/identity2.json` (the standard OVOS `NodeIdentity` file).
Populate it with:

```bash
hivemind-client set-identity \
  --host ws://192.168.1.10:5678 \
  --key  abc123... \
  --password def456...
```

Fields resolved from the identity file (CLI flags override):

| CLI flag | Identity field |
|----------|----------------|
| `--host` | `default_master` |
| `--key` | `access_key` |
| `--password` | `password` |
| `--port` | `default_port` |
| `--siteid` | `site_id` |

---

## OVOS configuration file

The satellite is built on top of
[ovos-dinkum-listener](https://openvoiceos.github.io/ovos-technical-manual/speech_service/)
and
[ovos-audio](https://openvoiceos.github.io/ovos-technical-manual/audio_service/).
All plugin selection and tuning happens in the standard OVOS config:

```
~/.config/mycroft/mycroft.conf
```

### Minimal example

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
    "ovos-stt-plugin-server": {
      "url": "https://stt.openvoiceos.org/stt"
    }
  },
  "tts": {
    "module": "ovos-tts-plugin-server",
    "ovos-tts-plugin-server": {
      "host": "https://tts.openvoiceos.org"
    }
  }
}
```

---

## Plugin slots

All plugin types are managed by
[ovos-plugin-manager](https://github.com/OpenVoiceOS/ovos-plugin-manager).
Install the plugin with `pip`, then set `module` in the config.

| Plugin type | Config key | Required | Default installed | Documentation |
|-------------|------------|:--------:|-------------------|---------------|
| Microphone | `microphone.module` | Yes | `ovos-microphone-plugin-alsa` (Linux) | [Mic plugins](https://openvoiceos.github.io/ovos-technical-manual/mic_plugins/) |
| VAD | `listener.VAD.module` | Yes | `ovos-vad-plugin-silero` | [VAD plugins](https://openvoiceos.github.io/ovos-technical-manual/vad_plugins/) |
| Wakeword | `listener.hey_mycroft.module` | Yes* | `ovos-ww-plugin-vosk` | [WW plugins](https://openvoiceos.github.io/ovos-technical-manual/ww_plugins/) |
| STT | `stt.module` | Yes | `ovos-stt-plugin-server` | [STT plugins](https://openvoiceos.github.io/ovos-technical-manual/stt_plugins/) |
| TTS | `tts.module` | Yes | `ovos-tts-plugin-server` | [TTS plugins](https://openvoiceos.github.io/ovos-technical-manual/tts_plugins) |
| G2P | `tts.g2p_module` | No | — | [G2P plugins](https://openvoiceos.github.io/ovos-technical-manual/g2p_plugins) |
| Audio transformers | `audio_transformers` (legacy: `listener.audio_transformers`) | No | — | [Transformer plugins](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| Dialog transformers | `dialog_transformers` | No | — | [Transformer plugins](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| TTS transformers | `tts_transformers` | No | — | [Transformer plugins](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| Media playback | `Audio.backends` | No | — | [Media playback plugins](https://openvoiceos.github.io/ovos-technical-manual/media_plugins/) |
| OCP | `ocp` | No | — | [OCP plugins](https://openvoiceos.github.io/ovos-technical-manual/ocp_plugins/) |
| PHAL | — | No | — | [PHAL](https://openvoiceos.github.io/ovos-technical-manual/PHAL/) |

\* Wakeword can be skipped by enabling [continuous listening mode](https://openvoiceos.github.io/ovos-technical-manual/speech_service/#modes-of-operation).

### Transformer pipelines in a split deployment

The satellite runs the full on-device pipeline stack: **audio transformers**
(listener, pre-STT), **dialog transformers** and **tts transformers**
(playback). **Utterance/metadata/intent transformers do not run here** —
they run server-side, in ovos-core behind the HiveMind server (and
hivemind-core can run its own utterance/metadata/dialog chains for the
mesh).

Enable each plugin in exactly one place: per-device effects (denoise,
speaker-specific audio tweaks) on the satellite; fleet-wide effects
(persona/tone rewrites, shared corrections, policy stop-words) on the
server. If TTS audio arrives saying different text than the skill produced,
a server-side dialog transformer is rewriting it — deliberate when
centralizing a persona, worth checking if unexpected. Full contract:
[ovos-plugin-manager transformer docs](https://github.com/OpenVoiceOS/ovos-plugin-manager/blob/dev/docs/transformers.md).

### Fully local example (no cloud calls)

```json
{
  "microphone": {
    "module": "ovos-microphone-plugin-alsa",
    "ovos-microphone-plugin-alsa": {
      "device_name": "hw:1,0"
    }
  },
  "listener": {
    "VAD": { "module": "ovos-vad-plugin-silero" },
    "wake_word": "hey_mycroft",
    "hey_mycroft": { "module": "ovos-ww-plugin-vosk" }
  },
  "stt": {
    "module": "ovos-stt-plugin-faster-whisper",
    "ovos-stt-plugin-faster-whisper": { "model": "small" }
  },
  "tts": {
    "module": "ovos-tts-plugin-piper",
    "ovos-tts-plugin-piper": { "voice": "en_US-lessac-medium" }
  }
}
```

### Continuous listening (no wakeword)

```json
{
  "listener": {
    "continuous_listen": true
  }
}
```

---

## PHAL

If `ovos-PHAL` is installed, the satellite starts it automatically alongside the voice loop. PHAL plugins provide platform-specific integrations (hardware buttons, LEDs, Mark 1 faceplate, etc.) and are configured under `PHAL` in `mycroft.conf`.
