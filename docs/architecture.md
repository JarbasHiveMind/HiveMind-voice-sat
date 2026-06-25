# Architecture

## On-device pipeline

```
Microphone (plugin)
      │  raw PCM frames
      ▼
   VAD (plugin)
      │  speech / silence decision
      ▼
 Wakeword engine (plugin)
      │  wakeword detected
      ▼
   STT (plugin)
      │  transcribed text utterance
      ▼
HiveMessageBusClient ──── WebSocket ──── HiveMind-core (hive)
                                               │
                             HiveMessage(utterance) → skill / intent system
                                               │
                             HiveMessage(speak / audio) ←
      ▼
   TTS (plugin)
      │  synthesized audio
      ▼
 Audio output (ovos-audio / PlaybackService)
```

Every stage runs **on this device**. The only data that crosses the network is:

- **Outbound:** a HiveMessage carrying the transcribed text utterance, wrapped in the standard HiveMind bus protocol, plus session metadata.
- **Inbound:** HiveMessages carrying `speak` (TTS text) or media playback instructions, which are handled locally by `ovos-audio`.

---

## Components

### `VoiceClient` (`service.py`)

Subclasses `OVOSDinkumVoiceService` from `ovos-dinkum-listener` with one override: `_connect_to_bus()` is a no-op. Instead of opening a local MessageBus WebSocket, the service receives a `HiveMessageBusClient` directly. This makes the OVOS voice loop transparently route messages through the HiveMind connection rather than a local bus.

### `PlaybackService` (`ovos-audio`)

Started alongside `VoiceClient`, also bound to the `HiveMessageBusClient`. Handles TTS playback and any media playback requests (OCP, audio backends) that the hive sends back. `validate_source=False` disables the local ACL check since all messages originate from the trusted hive connection.

### `HiveMessageBusClient`

Manages the authenticated WebSocket connection to `hivemind-core`. Handles:
- TLS (including `--selfsigned` bypass for self-signed certificates).
- `site_id` injection into every message's context for hive-side routing.
- Reconnection and session identity.

### PHAL (optional)

If `ovos-PHAL` is importable, it is started on the same `HiveMessageBusClient`. PHAL plugins can react to hardware events (buttons, displays) and publish messages that the hive receives as utterances or bus events.

---

## Wire protocol

HiveMind uses a WebSocket framing layer on top of the OVOS `Message` format. Each outbound utterance becomes a `HiveMessage` of type `bus` carrying an inner OVOS `recognizer_loop:utterance` message. The hive dispatches it to the skill / intent system exactly as if it were spoken locally.

Inbound messages follow the reverse path: a `speak` message from the hive arrives as a `HiveMessage`, the client unpacks it, and the local `PlaybackService` handles synthesis and audio output.

Session identity (`NodeIdentity`) provides:
- **Access key + password** — HMAC-based authentication, derived on connection.
- **Site ID** — written into `message.context.site_id` so the hive can address replies back to this satellite specifically.

---

## Full-local vs thinner satellites — trade-offs

| Factor | voice-sat (full local) | voice-relay | mic-satellite |
|--------|------------------------|-------------|---------------|
| Device compute | High | Medium | Low |
| Network bandwidth | Very low (text only) | Medium (post-wakeword audio) | High (raw audio) |
| Audio privacy | All audio stays on device | Audio after wakeword is sent | All audio sent |
| Server load | Minimal | STT + TTS only | STT + TTS + wakeword |
| Offline capability | Full (with local plugins) | Partial | Minimal |
| Latency | Depends on local model speed | STT round-trip | STT round-trip |

Full-local is the right choice when:
- Privacy regulations or user preference prohibit sending audio off-device.
- The device is on a slow or unreliable network link.
- The hive serves many clients and must not bear per-client STT/TTS load.

Thinner satellites are better when:
- The device cannot support local STT/TTS model inference (RAM, CPU).
- Centralized model management is preferred.
- Low device cost matters more than bandwidth efficiency.

---

## Dependency stack (the bus-client 2.x situation)

The satellite couples two dependency families that historically disagreed on the
`ovos-bus-client` major version:

- **OVOS runtime** — `ovos-audio` and `ovos-dinkum-listener` (plus
  `ovos-plugin-manager`) provide the on-device voice loop and playback service.
- **HiveMind transport** — `hivemind-bus-client` provides the
  `HiveMessageBusClient` that replaces the local MessageBus.

`hivemind-bus-client>=0.9.x` moved onto `ovos-bus-client>=2.0.0`. For a long time
the OVOS runtime capped `ovos-bus-client<2.0.0`, so the satellite was pinned to
the bus-client 1.x world to keep both families installable together. That cap is
now lifted:

| Package | First version supporting `ovos-bus-client` 2.x |
|---------|------------------------------------------------|
| `ovos-audio` | `1.2.3a1` (`>=1.3.0,<3.0.0`) |
| `ovos-dinkum-listener` | `0.7.2a1` (`>=1.3.4,<3.0.0`) |
| `ovos-plugin-manager` | `2.4.1a1` (`>=0.0.8,<3.0.0`) |

The whole stack therefore now resolves on the **bus-client 2.x line**, and
`pyproject.toml` pins these as prerelease *minimums* (e.g.
`ovos-plugin-manager>=2.4.1a1`) so `pip` selects them with **no `--pre` flag**.
Stable `ovos-plugin-manager==2.2.0` still caps `ovos-bus-client<2.0.0`, which is
why the floor is the `2.4.1a1` prerelease rather than `2.2.0`.
