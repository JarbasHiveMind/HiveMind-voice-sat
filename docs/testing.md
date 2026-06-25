# Testing

The suite is split into two tiers so the lightweight checks stay fast and the
heavyweight HiveMind-side round-trips don't drag the full alpha stack into every
CI matrix cell.

| Tier | Path | Extra | What it covers |
|------|------|-------|----------------|
| Smoke | `tests/test_smoke.py` | `[test]` | Packaging, version, the `VoiceClient` surface, console-script import. Network-free, no hivescope. |
| E2E | `tests/e2e/` | `[e2e]` | Real `hivemind-core` hub + real satellite client over a real `HiveMessageBusClient`, hardware mocked. |

## Running locally

Use a clean virtualenv (the e2e extra pulls the full 2.x alpha stack):

```bash
python3 -m venv .venv && . .venv/bin/activate

# smoke only (fast)
pip install -e ".[test]"
pytest tests/test_smoke.py

# full end-to-end suite
pip install -e ".[e2e]"
pytest tests/e2e/
```

No `--pre` is needed: the prerelease dependencies are pinned as minimum versions
in `pyproject.toml`, so pip resolves the 2.x stack on its own.

## How the e2e tests work

`tests/e2e/` boots a **real** `hivemind-core` hub in-process via
[hivescope](https://github.com/JarbasHiveMind/hivescope)'s loopback WebSocket
harness (`TopologyBuilder().add_master(use_loopback=True)`), registers a
satellite key, and connects the satellite over a **real**
`HiveMessageBusClient`. The HiveMind protocol, encryption handshake, ACL/policy
chain, and hub dispatch are all genuine production code over a localhost
WebSocket.

Only the **audio hardware** is mocked, and only at the seams that
`ovos-dinkum-listener` / `ovos-audio` already expose as constructor arguments:

- **Microphone** — a `FakeMicrophone` (silent fixed-size chunks).
- **STT** — a `FakeSTT` stub (utterances are injected on the bus directly).
- **VAD** — a `FakeVAD` reporting silence.
- **TTS** — a `CapturingTTS` that records synthesis requests instead of writing
  to a sound device. Injecting a TTS sets `PlaybackService.disable_reload`, so
  the real audio service never loads a real TTS plugin or opens an audio device.

There are **no** `importorskip` / `skipif` guards on missing dependencies — the
`[e2e]` extra is a hard requirement, so the tests always run.

### What the e2e suite asserts

- `test_satellite_hivemind_e2e.py` — the satellite-side round-trips:
  - an utterance on the satellite's real bus reaches the real hub agent bus with
    a stamped `source` (satellite → hub);
  - the real `VoiceClient` constructs and binds to the HiveMind bus with mocked
    hardware, and its `_connect_to_bus` no-op leaves the supplied bus in place;
  - a hub `speak` routed to the satellite peer drives the real `PlaybackService`
    and its injected fake TTS (hub → satellite).
- `test_bridge1_conformance.py` — OVOS-BRIDGE-1 / SESSION-1 conformance
  (envelope, source/destination, session fidelity, FIFO ordering).
- `test_acl_policy.py` — policy admission paths (allowed-types denial,
  skill-blacklist injection, reserved-session-id gate).

## CI

| Workflow | Job |
|----------|-----|
| `build_tests.yml` | smoke (`tests/test_smoke.py`, `[test]`) across Python 3.10–3.13 |
| `e2e_tests.yml` | e2e (`tests/e2e/`, `[e2e]`) on Python 3.11 |
| `coverage.yml` | full suite under coverage (`[e2e]`) |
| `lint.yml`, `pip_audit.yml`, `license_tests.yml`, `repo-health.yml` | static / supply-chain / health gates |

All jobs use the shared `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
