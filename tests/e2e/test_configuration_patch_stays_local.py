"""The satellite's configuration sync stays on the satellite.

ovos_config emits ``configuration.patch`` on ``Configuration.bus`` for every
``Configuration()[key] = value`` (ovos_config config.py ``__setitem__``), to
keep other local processes in sync. On a satellite every service shares one
process and one ``HiveMessageBusClient``, and ovos-audio's
``PlaybackService.init_messagebus`` binds ``Configuration.bus`` to that client.
So ``VoiceClient.__init__`` -> ``setup_locale()`` -> ``set_default_lang`` ->
``Configuration()["lang"] = ...`` sent the patch up to the hub:

* with a running bus the hub denied it (``configuration.patch`` is not a type a
  satellite may send, and a satellite must not patch the hub's configuration);
* with a bus not yet running, ``VoiceClient`` raised ``ValueError: You must
  execute run_forever() before emitting messages``.

A ``configuration.patch`` the hub sends down must still apply locally.

Real loopback hivemind-core hub, real HiveMessageBusClient, real
PlaybackService and VoiceClient; only mic/STT/VAD/TTS are fakes.
"""
import time
from unittest.mock import MagicMock

import pytest
from ovos_bus_client.message import Message
from ovos_config import Configuration
from hivemind_bus_client.client import HiveMessageBusClient

from hivemind_voice_satellite import VoiceClient

from test_satellite_hivemind_e2e import (
    CapturingTTS, FakeMicrophone, FakeSTT, FakeVAD, _connect_real_bus, _hub_with_satellite,
)

pytestmark = pytest.mark.timeout(120)


def _wait(pred, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture(autouse=True)
def _reset_configuration_bus():
    yield
    Configuration.deregister_bus()
    Configuration.bus = None


def _audio(bus):
    from ovos_audio.service import PlaybackService
    audio = PlaybackService(bus=bus, validate_source=False, tts=CapturingTTS(), disable_ocp=True)
    audio.playback = MagicMock()
    audio.daemon = True
    audio.start()
    return audio


def _stop(*services):
    for s in services:
        if s is None:
            continue
        try:
            (s.shutdown if hasattr(s, "shutdown") and not hasattr(s, "voice_loop") else s.stop)()
        except Exception:
            pass


def _spy_upstream(bus, msg_type):
    sent = []
    original = bus.emit

    def spy(message, *args, **kwargs):
        payload = getattr(message, "payload", message)
        if getattr(payload, "msg_type", None) == msg_type:
            sent.append(payload)
        return original(message, *args, **kwargs)

    bus.emit = spy
    return sent


def test_voiceclient_does_not_raise_before_the_bus_runs():
    """PlaybackService has bound Configuration to a client that is not running
    yet. Constructing VoiceClient must not try to send configuration.patch on
    it (dev: ValueError 'You must execute run_forever() before emitting')."""
    cold = HiveMessageBusClient(key="k", password="p", host="ws://127.0.0.1", port=1)
    audio = client = None
    try:
        audio = _audio(cold)
        client = VoiceClient(bus=cold, mic=FakeMicrophone(), stt=FakeSTT(), vad=FakeVAD())
    finally:
        _stop(client, audio)


def test_locale_and_later_config_writes_are_not_sent_to_the_hub():
    """In __main__ order (bus, PlaybackService, VoiceClient) no configuration.patch
    leaves the satellite and the hub denies nothing (dev: the lang patch went up
    and was denied)."""
    b, m = _hub_with_satellite(["recognizer_loop:utterance"])
    bus = audio = client = None
    try:
        bus = _connect_real_bus(m.network_protocol.url, useragent="sat-cfg")
        time.sleep(1)
        sent_up = _spy_upstream(bus, "configuration.patch")
        denied = []
        bus.internal_bus.on("hive.policy.denied", lambda msg: denied.append(msg.data.get("denied_type")))

        audio = _audio(bus)
        client = VoiceClient(bus=bus, mic=FakeMicrophone(), stt=FakeSTT(), vad=FakeVAD())
        Configuration()["t1014_probe"] = "stays-local"
        time.sleep(2)

        assert not sent_up, f"configuration.patch sent to the hub: {[p.data for p in sent_up]}"
        assert "configuration.patch" not in denied, denied
        assert Configuration()["t1014_probe"] == "stays-local"
    finally:
        _stop(client, audio)
        if bus is not None:
            bus.close()
        b.stop_all()


def test_a_configuration_patch_from_the_hub_still_applies():
    """Keeping the sync local must not stop the hub configuring the satellite:
    a configuration.patch the hub addresses to the satellite peer is applied."""
    b, m = _hub_with_satellite(["recognizer_loop:utterance"])
    bus = audio = client = None
    try:
        bus = _connect_real_bus(m.network_protocol.url, useragent="sat-cfg-down")
        time.sleep(1)
        peer = m.connected_peers()[0]
        audio = _audio(bus)
        client = VoiceClient(bus=bus, mic=FakeMicrophone(), stt=FakeSTT(), vad=FakeVAD())

        m.agent_protocol.bus.emit(Message(
            "configuration.patch", {"config": {"t1014_from_hub": "applied"}},
            {"destination": [peer]}))

        assert _wait(lambda: Configuration().get("t1014_from_hub") == "applied"), \
            "the hub's configuration.patch did not reach the satellite's Configuration"
    finally:
        _stop(client, audio)
        if bus is not None:
            bus.close()
        b.stop_all()
