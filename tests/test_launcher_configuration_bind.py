"""The launcher binds the configuration sync to the internal bus last.

``Configuration.bus`` is process-global and the last caller of
``Configuration.set_config_update_handlers`` wins. ``VoiceClient`` binds it
to ``bus.internal_bus``, but a service that the launcher starts after
``VoiceClient`` can bind it to the HiveMind client again. Then every
``Configuration()[key] = value`` sends ``configuration.patch`` to the hub.

The launcher must bind the sync to the internal bus after every service has
started, so a later bind cannot leak.
"""
import sys
import types
from unittest.mock import patch

from click.testing import CliRunner
from ovos_config import Configuration
from hivemind_bus_client.client import HiveMessageBusClient

import hivemind_voice_satellite.__main__ as launcher


class _Identity:
    password = "p"
    access_key = "k"
    site_id = "test"
    default_master = "ws://127.0.0.1"
    default_port = 1


class _Service:
    """A service that binds the configuration sync to the bus it gets, as
    ovos-audio PlaybackService does."""

    def __init__(self, bus=None, **kwargs):
        self.daemon = False
        Configuration.set_config_update_handlers(bus)

    def start(self):
        pass

    def stop(self):
        pass

    def shutdown(self):
        pass


class _VoiceClient(_Service):
    def __init__(self, bus=None, **kwargs):
        self.daemon = False
        Configuration.set_config_update_handlers(bus.internal_bus)


def test_a_service_started_after_voiceclient_cannot_leak_the_sync():
    seen = {}

    def exit_signal():
        seen["bus"] = Configuration.bus

    phal_module = types.ModuleType("ovos_PHAL.service")
    phal_module.PHAL = _Service  # started after VoiceClient, binds the hive client
    phal_pkg = types.ModuleType("ovos_PHAL")
    phal_pkg.service = phal_module

    try:
        with patch.object(launcher, "NodeIdentity", _Identity), \
                patch.object(HiveMessageBusClient, "connect", lambda self, *a, **k: None), \
                patch.object(launcher, "PlaybackService", _Service), \
                patch.object(launcher, "VoiceClient", _VoiceClient), \
                patch.object(launcher, "wait_for_exit_signal", exit_signal), \
                patch.dict(sys.modules, {"ovos_PHAL": phal_pkg, "ovos_PHAL.service": phal_module}):
            result = CliRunner().invoke(launcher.connect, [])
        assert result.exit_code == 0, result.output + repr(result.exception)
        assert seen["bus"] is not None
        assert not isinstance(seen["bus"], HiveMessageBusClient), \
            "Configuration.bus is the HiveMind client: configuration.patch goes to the hub"
    finally:
        Configuration.deregister_bus()
        Configuration.bus = None
