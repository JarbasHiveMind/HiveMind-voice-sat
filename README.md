# HiveMind Voice Satellite

OpenVoiceOS Satellite, connect to [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core)

![](./voice_terminal.png)

> NOTE: if you can't run TTS and STT locally, use [HiveMind-voice-relay](https://github.com/JarbasHiveMind/HiveMind-voice-relay) instead

## Install

Install dependencies (if needed)

```bash
sudo apt-get install -y libpulse-dev libasound2-dev
```

Install with pip (hivemind pypi version is VERY outdated)

```bash
$ pip install git+https://github.com/JarbasHiveMind/HiveMind-voice-sat
```

## Usage

```bash
Usage: hivemind-voice-sat [OPTIONS]

  connect to HiveMind

Options:
  --host TEXT      hivemind host
  --key TEXT       Access Key
  --password TEXT  Password for key derivation
  --port INTEGER   HiveMind port number
  --selfsigned     accept self signed certificates
  --help           Show this message and exit.

```


## Configuration

Voice satellite is built on top of [ovos-listener](https://openvoiceos.github.io/ovos-technical-manual/speech_service/) and [ovos-audio](https://openvoiceos.github.io/ovos-technical-manual/audio_service/), it uses the same OpenVoiceOS configuration `~/.config/mycroft/mycroft.conf`

Supported plugins:

| Plugin Type | Description | Required | Link |
|-------------|-------------|----------|------|
| Microphone | Captures voice input | Yes | [Microphone](https://openvoiceos.github.io/ovos-technical-manual/mic_plugins/) |
| VAD | Voice Activity Detection | Yes | [VAD](https://openvoiceos.github.io/ovos-technical-manual/vad_plugins/) |
| WakeWord | Detects wake words for interaction | Yes* | [WakeWord](https://openvoiceos.github.io/ovos-technical-manual/ww_plugins/) |
| STT | speech-to-text (STT)| Yes | [STT](https://openvoiceos.github.io/ovos-technical-manual/stt_plugins/) |
| TTS | text-to-speech (TTS) | Yes | [TTS](https://openvoiceos.github.io/ovos-technical-manual/tts_plugins) |
| Media Playback Plugins | Enables media playback (e.g., "play Metallica") | No | [Media Playback Plugins](https://openvoiceos.github.io/ovos-technical-manual/media_plugins/) |
| OCP Plugins | Provides playback support for URLs (e.g., YouTube) | No | [OCP Plugins](https://openvoiceos.github.io/ovos-technical-manual/ocp_plugins/) |
| Audio Transformers | Processes audio before speech-to-text (STT) | No | [Audio Transformers](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| Dialog Transformers | Processes text before text-to-speech (TTS) | No | [Dialog Transformers](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| TTS Transformers | Processes audio after text-to-speech (TTS) | No | [TTS Transformers](https://openvoiceos.github.io/ovos-technical-manual/transformer_plugins/) |
| PHAL | Provides platform-specific support (e.g., Mark 1) | No | [PHAL](https://openvoiceos.github.io/ovos-technical-manual/PHAL/) |

* can be skipped with [continuous listening mode](https://openvoiceos.github.io/ovos-technical-manual/speech_service/#modes-of-operation)


