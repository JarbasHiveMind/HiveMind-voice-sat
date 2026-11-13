"""The hub's legacy ``speak`` reaches the topic ovos-audio 2.x listens on.

ovos-audio 2.0.0 moved its audio output to the OVOS spec bus namespace
(ovos-audio#165): ``PlaybackService`` registers one listener, on
``ovos.utterance.speak``, and no longer listens on ``speak``. The hub still
sends ``speak`` over HiveMind, and the satellite delivers it on its internal
bus. The satellite can run on ovos-audio 2.x only because that bus
modernizes: a legacy topic also fires the spec twin. This pins that, so a
bus that stops modernizing is caught here and not by a silent satellite.
"""
from unittest.mock import MagicMock

from ovos_bus_client.message import Message


def _client():
    from hivemind_bus_client.client import HiveMessageBusClient
    identity = MagicMock()
    identity.password = "correct-horse-battery-staple-92"
    identity.access_key = "sat-key"
    identity.default_master = "ws://hub"
    identity.default_port = 5678
    identity.site_id = "site"
    return HiveMessageBusClient(identity=identity, host="ws://hub", port=5678,
                                key="sat-key", password="correct-horse-battery-staple-92")


def test_a_legacy_speak_from_the_hub_fires_the_spec_listener_ovos_audio_2_registers():
    bus = _client()
    seen = []
    bus.on("ovos.utterance.speak", lambda m: seen.append(m))
    # what a BUS frame from the hub becomes on the satellite's internal bus
    bus.internal_bus.emit(Message("speak", {"utterance": "hello"}))
    assert [m.msg_type for m in seen] == ["ovos.utterance.speak"]
    assert seen[0].data["utterance"] == "hello"


def test_playback_service_still_takes_the_arguments_the_launcher_passes():
    """PlaybackService(bus=..., validate_source=False) is the launcher's call
    (and the e2e adds tts= and disable_ocp=); the 2.x constructor keeps them."""
    import inspect
    from ovos_audio.service import PlaybackService
    params = inspect.signature(PlaybackService.__init__).parameters
    for name in ("bus", "validate_source", "tts", "disable_ocp"):
        assert name in params, name
    assert callable(getattr(PlaybackService, "_resolve_sound_uri", None))
