# HiveMind-voice-sat — agent guide

OpenVoiceOS voice satellite that runs STT/TTS/wake-word locally and uses a HiveMind
connection as its message bus instead of a local MycroftBus.

## Setup

```bash
pip install .
# platform extras for the microphone backend:
pip install .[linux]   # or .[mac]
```

`pyproject.toml` is the single packaging source of truth (no `requirements/`,
no `setup.py`). Runtime deps run on the `ovos-bus-client` 2.x line; prerelease
deps are pinned as minimum versions so pip resolves them without `--pre`.

Runtime config is the shared OVOS config at `~/.config/mycroft/mycroft.conf`.
Connection identity (key/password/host/site_id) comes from `NodeIdentity`
(`~/.config/hivemind/_identity.json`), or CLI flags, or ggwave audio pairing.

## Test

```bash
pip install .[test]   && pytest tests/test_smoke.py   # fast, no hivescope
pip install .[e2e]    && pytest tests/e2e/            # real hub + client
```

Two tiers: `tests/test_smoke.py` (network-free, `[test]` extra) runs across the
full Python matrix in `build_tests.yml`; `tests/e2e/` (`[e2e]` extra) boots a
real `hivemind-core` hub via `hivescope`'s loopback WebSocket and drives the
real satellite client over a real `HiveMessageBusClient`, mocking only the
audio hardware (mic/STT/VAD/TTS fakes injected via the service constructors).
The `[e2e]` extra declares `hivescope` + the 2.x stack — no `importorskip`.
See `docs/testing.md`.

## Lint/Typecheck

None configured.

## Layout

- `hivemind_voice_satellite/__main__.py` — `connect` Click command (the
  `hivemind-voice-sat` console entry point). Resolves identity, optionally runs
  ggwave pairing, opens a `HiveMessageBusClient`, then starts `PlaybackService`
  (ovos-audio), the `VoiceClient` listener, and optional `ovos_PHAL`.
- `hivemind_voice_satellite/service.py` — `VoiceClient`, a subclass of
  `OVOSDinkumVoiceService` whose `_connect_to_bus` is a no-op so the supplied
  HiveMind bus is used in place of the local bus.
- `hivemind_voice_satellite/version.py` — semver block (do not edit).
- Entry-point group: `console_scripts` (this is an application, not an OPM plugin).

## Conventions

- Branches: `dev` (work) and `master` (stable). NEVER use `main`.
- Never edit `version.py`; gh-automations bumps semver from conventional-commit
  prefixes (`feat:` / `fix:` / `feat!:`).
- New repos private by default.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- Reference `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary (no history, no dates) in docs, commits, code comments.
- CI is provided by OpenVoiceOS/gh-automations.

## Gotchas

- The bus is HiveMind, not a local MycroftBus: `VoiceClient._connect_to_bus` and
  `validate_source=False` exist precisely to bypass local-bus assumptions.
- If you cannot run STT/TTS locally, the intended alternative is
  `HiveMind-voice-relay`, not this package.
- CI is all `OpenVoiceOS/gh-automations` reusable workflows at `@dev`
  (`build_tests`, `e2e_tests`, `coverage`, `lint`, `pip_audit`, `license_tests`,
  `repo-health`, release/publish). The license check excludes the project's own
  HiveMind/OVOS copyleft family.
