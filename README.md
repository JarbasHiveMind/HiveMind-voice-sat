# HiveMind Voice Satellite

OpenVoiceOS Satellite, connect to [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core)

![](./voice_terminal.png)

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

Voice satellite uses the default OpenVoiceOS configuration `~/.config/mycroft/mycroft.conf`

Supported plugin types:
- Microphone  (required)
- VAD  (required)
- WakeWord (required)
- STT  (required)
- TTS  (required)
- Audio Transformers  (optional, None by default)
- Dialog Transformers  (optional, None by default)
- TTS Transformers  (optional, None by default)
- PHAL  (optional, None by default)