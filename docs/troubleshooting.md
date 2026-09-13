# Troubleshooting

## Connection problems

### `RuntimeError: NodeIdentity not set`

No credentials were supplied via CLI flags and the identity file is missing or incomplete.

Fix:

```bash
hivemind-client set-identity \
  --host ws://your-hive-host:5678 \
  --key YOUR_ACCESS_KEY \
  --password YOUR_PASSWORD
```

Or pass `--host`, `--key`, and `--password` directly on the command line.

---

### `Invalid host, please specify a protocol`

The host string did not start with `ws://` or `wss://`. The satellite auto-prepends `ws://` when it detects no protocol. Check the value you passed. If it contains `https://` or a stray character, the auto-fix does not apply.

Fix: use `--host ws://192.168.1.10:5678` or `--host wss://myhive.example.com:5678`.

---

### TLS / SSL handshake errors (`wss://`)

If the hive uses a self-signed certificate, pass `--selfsigned`:

```bash
hivemind-voice-sat --host wss://myhive.local:5678 --selfsigned
```

For a CA-signed certificate that still fails: verify the system CA bundle is up to date (`sudo update-ca-certificates` on Debian/Ubuntu).

---

### Connects then immediately disconnects

- Wrong access key or password. Regenerate with `hivemind-core add-client` on the hive.
- The client entry was deleted on the hive. Re-add it.
- A firewall blocks port 5678. Check both ends.

---

## No audio input (microphone)

### Satellite starts but never hears the wakeword

1. Confirm the mic is visible to the OS:
   ```bash
   arecord -l
   ```
2. Record a short clip to confirm the mic works:
   ```bash
   arecord -d 3 -f cd /tmp/test.wav && aplay /tmp/test.wav
   ```
3. Check the `microphone.module` in `mycroft.conf`. If the plugin is missing, install it:
   ```bash
   pip install ovos-microphone-plugin-alsa        # Linux ALSA
   pip install ovos-microphone-plugin-sounddevice  # cross-platform
   ```
4. If using ALSA, set `device_name` explicitly (see [Deployment](deployment.md)).
5. Ensure the running user is in the `audio` group:
   ```bash
   groups $USER   # should include "audio"
   sudo usermod -aG audio $USER
   ```

### `TypeError: 'NoneType' object is not callable` when the listener starts

The base package installs no microphone plugin. The default configuration asks for
`ovos-microphone-plugin-alsa`, and when no microphone plugin is installed the listener
fails with this `TypeError`, which does not name the missing plugin. Install a
microphone backend, for example with the `[linux]` or `[mac]` extra above.

### A device with no audio hardware

A test box or CI runner has no microphone. `ovos-microphone-plugin-files` reads WAV
files instead: it watches `~/file_microphone`, reads each file dropped there as
microphone input, and then deletes it.

```bash
pip install --pre ovos-microphone-plugin-files
```

```json
{ "listener": { "microphone": { "module": "ovos-microphone-plugin-files" } } }
```

---

## Wakeword not triggering

1. The wakeword plugin this package installs is `ovos-ww-plugin-vosk`. Verify it is installed:
   ```bash
   pip show ovos-ww-plugin-vosk
   ```
2. Check the configured wakeword phrase matches what you are saying. Default is *Hey Mycroft*.
3. Increase microphone gain or move closer. VAD may be clipping quiet speech.
4. Try disabling the wakeword with continuous listening to isolate whether the issue is wakeword-specific:
   ```json
   { "listener": { "continuous_listen": true } }
   ```
5. `ImportError: Wake Word hey_mycroft_precise with module ovos-ww-plugin-precise failed to load`
   at startup means the configuration names the precise plugin, which is not installed. The
   stock OVOS configuration does this unless `mycroft.conf` sets `hey_mycroft` to
   `ovos-ww-plugin-vosk` as in the [README](../README.md). OVOS then loads the vosk fallback,
   so the wakeword can still work. Set the vosk module in `mycroft.conf` to stop the error.
6. The vosk plugin downloads its language model from `alphacephei.com` on its first start.
   A device with no internet access at that moment has no wakeword. Give it network access
   for the first start, or copy the model into `~/.local/share/vosk/` beforehand.

---

## STT not working

### Satellite transcribes silence or garbage

- Default STT is `ovos-stt-plugin-server` pointing to a remote endpoint. If the endpoint is unreachable, transcription fails silently.
- Switch to a fully local plugin for testing:
  ```bash
  pip install ovos-stt-plugin-faster-whisper
  ```
  ```json
  { "stt": { "module": "ovos-stt-plugin-faster-whisper",
             "ovos-stt-plugin-faster-whisper": { "model": "tiny" } } }
  ```

### STT plugin import error

Plugin name in `stt.module` does not match the installed package entry point. Run:

```bash
ovos-plugin-manager --list stt
```

to see available STT plugins.

---

## No audio output (TTS)

### Responses arrive but nothing is spoken

1. Test the system audio output:
   ```bash
   speaker-test -t wav -c 2
   ```
2. Check `tts.module` in `mycroft.conf`. Default is `ovos-tts-plugin-server`.
3. For a local TTS test:
   ```bash
   pip install ovos-tts-plugin-piper
   ```
   ```json
   { "tts": { "module": "ovos-tts-plugin-piper",
              "ovos-tts-plugin-piper": { "voice": "en_US-lessac-medium" } } }
   ```
4. On headless Pi, ensure ALSA default output is set (see [Deployment](deployment.md)).

---

## STT/TTS model download failures

Plugins that download models on first use (Vosk, Faster-Whisper, Piper) write to `~/.local/share/` by default. Ensure there is enough disk space:

```bash
df -h ~/.local
```

If the download fails midway, delete the partial model directory and restart. For offline environments, pre-download the models and configure the plugin to use the local path. Consult the individual plugin's README.

---

## Logs

Default log level is `INFO`. Increase verbosity:

```json
{ "log_level": "DEBUG" }
```

Log output goes to the terminal. When running under systemd:

```bash
sudo journalctl -u hivemind-voice-sat -f
```

---
[← Deployment](deployment.md) · [Home](index.md) · [Testing →](testing.md)
