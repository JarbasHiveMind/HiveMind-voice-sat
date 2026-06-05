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

The host string did not start with `ws://` or `wss://`. The satellite auto-prepends `ws://` if no protocol is detected, but check the value you passed — if it contains `https://` or a stray character the auto-fix does not apply.

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

- Wrong access key or password — regenerate with `hivemind-core add-client` on the hive.
- The client entry was deleted on the hive — re-add it.
- Firewall blocking port 5678 — check both ends.

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
3. Check the `microphone.module` in `mycroft.conf` — if the plugin is missing, install it:
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

---

## Wakeword not triggering

1. The default wakeword plugin is `ovos-ww-plugin-vosk`. Verify it is installed:
   ```bash
   pip show ovos-ww-plugin-vosk
   ```
2. Check the configured wakeword phrase matches what you are saying. Default is *Hey Mycroft*.
3. Increase microphone gain or move closer; VAD may be clipping quiet speech.
4. Try disabling the wakeword with continuous listening to isolate whether the issue is wakeword-specific:
   ```json
   { "listener": { "continuous_listen": true } }
   ```

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

If the download fails midway, delete the partial model directory and restart. For offline environments, pre-download models and configure the plugin to use the local path — consult the individual plugin's README.

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
