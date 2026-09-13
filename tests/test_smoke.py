"""Network-free smoke tests.

These run across the full python matrix in build_tests with only the
lightweight ``[test]`` extra. They exercise packaging and the satellite's own
code surface without booting a hivemind-core hub or any audio hardware — the
heavyweight HiveMind-side round-trips live in ``tests/e2e/`` and run in the
dedicated e2e job with the ``[e2e]`` extra.
"""
from unittest.mock import MagicMock


def test_version_importable():
    from hivemind_voice_satellite.version import __version__
    assert __version__
    # dynamic version comes from the VERSION_BLOCK, e.g. "2.1.0a1"
    assert __version__[0].isdigit()


def test_voiceclient_exported():
    """The package exposes VoiceClient (the ovos-dinkum-listener subclass)."""
    from hivemind_voice_satellite import VoiceClient
    from hivemind_voice_satellite.service import VoiceClient as ServiceVoiceClient
    assert VoiceClient is ServiceVoiceClient


def test_voiceclient_connect_to_bus_is_noop():
    """VoiceClient._connect_to_bus must be a no-op so the supplied HiveMind bus
    is used in place of a local MycroftBus — the defining trait of the satellite.
    """
    from hivemind_voice_satellite.service import VoiceClient
    instance = VoiceClient.__new__(VoiceClient)
    sentinel = MagicMock()
    instance.bus = sentinel
    # must not raise and must not replace the bus
    assert VoiceClient._connect_to_bus(instance) is None
    assert instance.bus is sentinel


def test_connect_entrypoint_importable():
    """The console-script target imports without side effects."""
    from hivemind_voice_satellite.__main__ import connect
    assert callable(connect)
