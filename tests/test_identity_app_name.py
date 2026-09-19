"""The identity is this application's own (HIVEMIND-CRYPTO-1 §2).

Before this change the entry point called ``NodeIdentity()`` and shared
``~/.config/hivemind/_identity.json`` with every other HiveMind application of
the user, so a satellite, a bridge and the CLI on one account presented one
identifier and one static key. The application now names itself, and hands that identity to the client:
without ``identity=`` the client builds ``NodeIdentity()`` itself and presents
the shared Noise and RSA keys under this application's access key.
"""
from unittest.mock import MagicMock, patch

import pytest

APP_NAME = "voice-sat"


def _identity():
    identity = MagicMock()
    identity.password = "correct-horse-battery-staple-92"
    identity.access_key = "sat-key"
    identity.site_id = "site"
    identity.default_master = "ws://hub"
    identity.default_port = 5678
    return identity


class _Stop(Exception):
    """Raised by the patched client's connect(): the run ends right after
    the client is built, which is all these tests look at."""


def test_the_satellite_asks_for_its_own_identity_and_hands_it_to_the_client():
    from hivemind_voice_satellite import __main__ as entry
    from click.testing import CliRunner
    identity = _identity()
    with patch.object(entry, "NodeIdentity", return_value=identity) as ctor, \
         patch.object(entry, "HiveMessageBusClient") as client:
        client.return_value.connect.side_effect = _Stop
        result = CliRunner().invoke(entry.connect, [])
    ctor.assert_called_once_with(app_name=APP_NAME)
    assert isinstance(result.exception, _Stop), result.output
    assert client.call_args.kwargs.get("identity") is identity, (
        "the client was built without the application's identity")
