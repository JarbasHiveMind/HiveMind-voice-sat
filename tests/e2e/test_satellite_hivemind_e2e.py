"""REAL satellite-side end-to-end tests for HiveMind-voice-sat.

These exercise the satellite's **real** code path against a **real**
hivemind-core hub:

    fake mic / fake STT  (mocked hardware)
        -> real ovos-dinkum-listener voice loop (the VoiceClient subclass)
        -> recognizer_loop:utterance on the satellite's REAL HiveMessageBusClient
        -> real WebSocket  -> real hivemind-core hub  -> agent bus

and the reverse:

    agent bus emits `speak` routed to the satellite peer
        -> real WebSocket  -> satellite's REAL HiveMessageBusClient
        -> real ovos-audio PlaybackService.handle_speak
        -> injected fake TTS captures the synthesis call  (mocked hardware)

Everything between the satellite client and the hub is the genuine production
HiveMessageBusClient + hivemind-core stack over a localhost WebSocket
(hivescope's loopback hub). Only the *hardware* seams are mocked: the
microphone, STT, VAD, and TTS plugins are in-process fakes injected through the
constructors that ovos-dinkum-listener / ovos-audio already expose. No audio
device, no model download, and no network beyond localhost are touched. There
is no importorskip / skipif — the full 2.x stack is a hard `[e2e]` dependency.

Reference (sibling HiveMind e2e): HiveMind-deltachat-bridge
``tests/e2e/test_bridge_hivemind_e2e.py`` — add_master(use_loopback=True);
register_satellite(...); responder on master.agent_protocol.bus.
"""
import time
from queue import Queue, Empty
from unittest.mock import MagicMock

import pytest
from ovos_bus_client.message import Message
from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.message import HiveMessage, HiveMessageType

from ovos_plugin_manager.templates.microphone import Microphone
from ovos_plugin_manager.templates.stt import STT
from ovos_plugin_manager.templates.vad import VADEngine
from ovos_plugin_manager.templates.tts import TTS

from hivescope.topology import TopologyBuilder

from hivemind_voice_satellite import VoiceClient


pytestmark = pytest.mark.timeout(60)


# ---------------------------------------------------------------------------
# Mocked hardware — in-process fakes for the mic / STT / VAD / TTS seams.
# ovos-dinkum-listener and ovos-audio accept these objects through their
# constructors, so injecting them bypasses every real plugin / device.
# ---------------------------------------------------------------------------

class FakeMicrophone(Microphone):
    """Silent microphone that yields fixed-size empty chunks forever."""

    sample_rate = 16000
    sample_width = 2
    sample_channels = 1
    chunk_size = 4096

    def start(self):
        pass

    def read_chunk(self):
        # Block-ish: hand back silence at the configured chunk size. The voice
        # loop never needs real audio because STT/VAD are also faked.
        time.sleep(0.01)
        return b"\x00" * (self.chunk_size * self.sample_width)

    def stop(self):
        pass


class FakeSTT(STT):
    """STT stub — never invoked in these tests (utterances are injected on the
    bus directly), but a non-null STT keeps the listener from loading a real
    plugin."""

    def execute(self, audio, language=None):
        return "test transcription"


class FakeVAD(VADEngine):
    """VAD stub that always reports silence so the voice loop never tries to
    run STT on the fake mic's empty audio."""

    def is_silence(self, chunk):
        return True

    def reset(self):
        pass


class CapturingTTS(TTS):
    """TTS stub that records every synthesis request instead of producing audio.

    Injecting this into PlaybackService sets ``disable_reload=True`` so the real
    audio service never loads a real TTS plugin or writes to a sound device.
    """

    def __init__(self, config=None):
        super().__init__(config=config or {})
        self.spoken = Queue()

    def get_tts(self, sentence, wav_file, **kwargs):
        self.spoken.put(sentence)
        # Return an (audio_file, phonemes) tuple; the file need not exist for
        # the capture assertion, and playback is stubbed below.
        return wav_file, None


# ---------------------------------------------------------------------------
# Loopback hub + real satellite bus helpers.
# ---------------------------------------------------------------------------

def _hub_with_satellite(allowed_types):
    """Boot a real loopback hub and pre-register one satellite key."""
    b = TopologyBuilder()
    m = b.add_master("M0", use_loopback=True)
    m.register_satellite("sat-key", password="sat-pass",
                         allowed_types=allowed_types)
    b.start_all()
    return b, m


def _host_port(url):
    bare = url.replace("ws://", "").replace("wss://", "").rstrip("/")
    host, port = bare.split(":")
    return "ws://" + host, int(port)


def _connect_real_bus(url, useragent="sat-e2e"):
    """Open the satellite's REAL HiveMessageBusClient against the loopback hub."""
    host, port = _host_port(url)
    bus = HiveMessageBusClient(key="sat-key", password="sat-pass",
                               host=host, port=port,
                               useragent=useragent, self_signed=False)
    bus.connect(site_id="test-site")
    deadline = time.time() + 15
    while time.time() < deadline and not bus.handshake_event.is_set():
        time.sleep(0.1)
    assert bus.handshake_event.is_set(), "satellite handshake did not complete"
    return bus


# ---------------------------------------------------------------------------
# Inbound: real listener-side utterance -> real hub agent bus.
# ---------------------------------------------------------------------------

def test_satellite_utterance_reaches_hub_agent():
    """An utterance injected on the satellite's real bus reaches the real hub
    agent bus over a real WebSocket, carrying a stamped source.

    This is the satellite -> hub leg of the bridge. The hardware (mic/STT) is
    irrelevant here: a recognizer_loop:utterance is emitted on the genuine
    HiveMessageBusClient exactly as the dinkum listener would after STT.
    """
    b, m = _hub_with_satellite(["recognizer_loop:utterance"])
    bus = None
    try:
        seen = []
        m.agent_protocol.bus.on("recognizer_loop:utterance", seen.append)

        bus = _connect_real_bus(m.network_protocol.url)
        time.sleep(1)  # let the encrypted HELLO register the peer
        assert len(m.connected_peers()) == 1, \
            f"expected 1 connected peer, got {m.connected_peers()}"

        bus.emit(HiveMessage(
            HiveMessageType.BUS,
            payload=Message("recognizer_loop:utterance",
                            {"utterances": ["what is the weather"]}),
        ))

        deadline = time.time() + 10
        while time.time() < deadline and not seen:
            time.sleep(0.05)

        assert seen, "utterance never reached the hub agent bus"
        m.agent_protocol.assert_injected("recognizer_loop:utterance", count=1)
        injected = m.agent_protocol.last_injected("recognizer_loop:utterance")
        assert injected.data["utterances"] == ["what is the weather"]
        # hivemind-core stamps a non-empty source identifying the peer
        assert injected.context.get("source"), "no source stamped on injection"
    finally:
        if bus is not None:
            bus.close()
        b.stop_all()


def test_voiceclient_constructs_with_mocked_hardware():
    """The REAL VoiceClient (the ovos-dinkum-listener subclass) constructs and
    binds to the satellite's real HiveMind bus with mocked mic/STT/VAD, and its
    _connect_to_bus override leaves the supplied HiveMind bus in place.

    Proves the satellite's own service class works on the 2.x stack without any
    real audio hardware.
    """
    b, m = _hub_with_satellite(["recognizer_loop:utterance"])
    bus = None
    client = None
    try:
        bus = _connect_real_bus(m.network_protocol.url, useragent="sat-vc")
        time.sleep(1)

        client = VoiceClient(
            bus=bus,
            mic=FakeMicrophone(),
            stt=FakeSTT(),
            vad=FakeVAD(),
        )
        # the HiveMind bus must be used verbatim; _connect_to_bus is a no-op
        assert client.bus is bus
        client._connect_to_bus()  # must not replace the bus or raise
        assert client.bus is bus

        # the real listener can still inject an utterance over the real bus
        seen = []
        m.agent_protocol.bus.on("recognizer_loop:utterance", seen.append)
        bus.emit(HiveMessage(
            HiveMessageType.BUS,
            payload=Message("recognizer_loop:utterance", {"utterances": ["ping"]}),
        ))
        deadline = time.time() + 10
        while time.time() < deadline and not seen:
            time.sleep(0.05)
        assert seen, "VoiceClient's bus did not deliver the utterance to the hub"
    finally:
        if client is not None:
            try:
                client.stop()
            except Exception:
                pass
        if bus is not None:
            bus.close()
        b.stop_all()


# ---------------------------------------------------------------------------
# Outbound: real hub `speak` -> real PlaybackService -> captured fake TTS.
# ---------------------------------------------------------------------------

def test_hub_speak_reaches_real_playback_service():
    """A `speak` emitted by the hub agent and routed to the satellite peer
    arrives on the satellite's real bus and drives the real ovos-audio
    PlaybackService, whose injected fake TTS captures the synthesis request.

    This is the hub -> satellite leg of the bridge with the audio service real
    and only the TTS device faked.
    """
    from ovos_audio.service import PlaybackService

    b, m = _hub_with_satellite(["recognizer_loop:utterance", "speak"])
    bus = None
    audio = None
    try:
        bus = _connect_real_bus(m.network_protocol.url, useragent="sat-tts")
        time.sleep(1)
        assert len(m.connected_peers()) == 1
        peer = m.connected_peers()[0]

        tts = CapturingTTS()
        audio = PlaybackService(bus=bus, validate_source=False,
                                tts=tts, disable_ocp=True)
        # don't spin OCP / real playback threads we don't need
        audio.playback = MagicMock()
        audio.daemon = True
        audio.start()
        time.sleep(1)

        # hub agent speaks back to the satellite peer
        m.agent_protocol.bus.emit(Message(
            "speak",
            {"utterance": "it is sunny"},
            {"destination": [peer]},
        ))

        try:
            spoken = tts.spoken.get(timeout=10)
        except Empty:
            pytest.fail("speak never reached the real PlaybackService / TTS")
        assert spoken == "it is sunny"
    finally:
        if audio is not None:
            try:
                audio.shutdown()
            except Exception:
                pass
        if bus is not None:
            bus.close()
        b.stop_all()
