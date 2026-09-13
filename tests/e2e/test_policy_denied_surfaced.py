"""A denial from the hub reaches the satellite's user, not only its log.

HIVEMIND-POLICY-1 §6: "When the chain denies a message, the client **MUST**
receive a `BUS` message reporting the denial. The Layer-1 message type of that
payload is **`hive.policy.denied`**." and "A client **SHOULD** branch on
`code`; `reason` is informational and **MUST NOT** be parsed for control flow."

Before this test the satellite logged ``BUS: hive.policy.denied`` at INFO and
did nothing else, so a user whose utterance was denied heard silence.

Real loopback hivemind-core hub, real HiveMessageBusClient, real VoiceClient;
only the mic/STT/VAD hardware seams are faked (as in
test_satellite_hivemind_e2e.py).
"""
import os
import time
from unittest.mock import patch

import pytest
from ovos_bus_client.message import Message
from hivemind_bus_client.message import HiveMessage, HiveMessageType

import hivemind_voice_satellite.service as service
from hivemind_voice_satellite import VoiceClient

from test_satellite_hivemind_e2e import (
    FakeMicrophone, FakeSTT, FakeVAD, _connect_real_bus, _hub_with_satellite,
)

pytestmark = pytest.mark.timeout(60)


def _wait(pred, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture
def denying_hub_and_client():
    # the hub admits nothing: every message from this satellite is denied
    # with acl_disallowed_type
    b, m = _hub_with_satellite([])
    bus = client = None
    try:
        bus = _connect_real_bus(m.network_protocol.url, useragent="sat-denied")
        time.sleep(1)
        client = VoiceClient(bus=bus, mic=FakeMicrophone(), stt=FakeSTT(), vad=FakeVAD())
        yield m, bus, client
    finally:
        if client is not None:
            try:
                client.stop()
            except Exception:
                pass
        if bus is not None:
            bus.close()
        b.stop_all()


def _capture_local(bus, msg_type):
    seen = []
    bus.internal_bus.on(msg_type, seen.append)
    return seen


def _warnings(mock_warning):
    return [" ".join(str(a) for a in call.args) for call in mock_warning.call_args_list]


def test_denied_utterance_plays_error_sound_locally(denying_hub_and_client):
    """A denied utterance plays the error sound on the satellite's own bus and
    logs the denial at WARNING with its denied type and code."""
    m, bus, client = denying_hub_and_client
    sounds = _capture_local(bus, "mycroft.audio.play_sound")
    denials = _capture_local(bus, "hive.policy.denied")

    with patch.object(service.LOG, "warning") as warning:
        bus.emit(HiveMessage(HiveMessageType.BUS, payload=Message(
            "recognizer_loop:utterance", {"utterances": ["what time is it"]})))
        assert _wait(lambda: denials), "the hub never sent hive.policy.denied"
        assert denials[0].data.get("code") == "acl_disallowed_type"
        assert _wait(lambda: sounds), \
            "a denied utterance produced no sound: the user hears silence"
        warned = [w for w in _warnings(warning) if "acl_disallowed_type" in w]

    uri = sounds[0].data.get("uri")
    assert uri == service._denied_sound_uri()
    # the real audio service must be able to open it, or the user still
    # hears nothing
    from ovos_audio.service import PlaybackService
    assert os.path.isfile(PlaybackService._resolve_sound_uri(uri))
    assert warned, "the denial was not logged at WARNING with its code"
    assert "recognizer_loop:utterance" in warned[0]


def test_denied_background_type_is_logged_not_sounded(denying_hub_and_client):
    """A denied non-utterance type (the listener's volume query) is logged at
    WARNING but plays no sound, so background plumbing does not beep at the
    user on every turn."""
    m, bus, client = denying_hub_and_client
    sounds = _capture_local(bus, "mycroft.audio.play_sound")
    denials = _capture_local(bus, "hive.policy.denied")

    with patch.object(service.LOG, "warning") as warning:
        bus.emit(HiveMessage(HiveMessageType.BUS, payload=Message("mycroft.volume.get", {})))
        assert _wait(lambda: denials), "the hub never sent hive.policy.denied"
        time.sleep(0.5)
        warned = [w for w in _warnings(warning)
                  if "mycroft.volume.get" in w and "acl_disallowed_type" in w]

    assert not sounds, f"a background denial played a sound: {sounds[0].data}"
    assert warned, "the background denial was not logged at WARNING with its code"
