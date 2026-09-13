import os

import ovos_dinkum_listener
from hivemind_bus_client.client import HiveMessageBusClient
from ovos_bus_client.message import Message
from ovos_dinkum_listener.service import OVOSDinkumVoiceService
from ovos_utils.log import LOG
from ovos_config.locale import setup_locale


def on_ready():
    LOG.info('HiveMind Voice Satellite is ready.')


def on_started():
    LOG.info('HiveMind Voice Satellite started.')


def on_alive():
    LOG.info('HiveMind Voice Satellite alive.')


def on_stopping():
    LOG.info('HiveMind Voice Satellite is shutting down...')


def on_error(e='Unknown'):
    LOG.error(f'HiveMind Voice Satellite failed to launch ({e}).')


# A denial of one of these is the silence a user notices: they spoke and
# nothing happened. Denials of the listener's background traffic (volume,
# mic status) are logged only, so they do not sound on every turn.
USER_FACING_TYPES = frozenset({"recognizer_loop:utterance", "ovos.utterance.handle"})
DENIED_SOUND = "snd/error.mp3"


def _denied_sound_uri() -> str:
    """The error sound as an absolute path from ovos-dinkum-listener.

    ovos-audio resolves a bare ``snd/`` URI only against its own ``res``
    directory, which not every ovos-audio release ships, and raises
    FileNotFoundError when it is missing. The listener this satellite
    depends on always carries the file, so send its full path.
    """
    path = os.path.join(os.path.dirname(ovos_dinkum_listener.__file__), "res", DENIED_SOUND)
    return path if os.path.isfile(path) else DENIED_SOUND


class VoiceClient(OVOSDinkumVoiceService):
    """HiveMind Voice Satellite, but bus is replaced with hivemind connection"""

    def __init__(self, bus: HiveMessageBusClient, on_ready=on_ready, on_error=on_error,
                 on_stopping=on_stopping, on_alive=on_alive,
                 on_started=on_started, watchdog=lambda: None, mic=None, **kwargs):
        setup_locale()  # read mycroft.conf for default lang/timezone in all modules (eg, lingua_franca)
        # **kwargs is forwarded to OVOSDinkumVoiceService so callers may inject
        # stt / vad / hotwords (e.g. tests passing in-process fakes).
        super().__init__(on_ready, on_error, on_stopping, on_alive, on_started, watchdog, mic,
                         bus=bus, validate_source=False, **kwargs)
        self.bus.on("hive.policy.denied", self.handle_policy_denied)

    def handle_policy_denied(self, message: Message):
        """Tell the user the hub refused what the satellite sent.

        HIVEMIND-POLICY-1 §6: the hub reports a denial as a BUS message of
        type ``hive.policy.denied`` carrying ``denied_type``, ``code`` and
        ``reason``. ``reason`` is for logs only and is never parsed.

        Every denial is logged at WARNING. A denied user utterance also plays
        the error sound, on the satellite's own bus: sending it to the hub
        would only be denied again.
        """
        data = message.data or {}
        denied_type = data.get("denied_type") or "unknown"
        code = data.get("code") or "unknown"
        LOG.warning(f"HiveMind hub denied '{denied_type}' (code={code}): "
                    f"{data.get('reason') or 'no reason given'}")
        if denied_type in USER_FACING_TYPES:
            self.bus.internal_bus.emit(Message("mycroft.audio.play_sound",
                                               {"uri": _denied_sound_uri()}))

    def _connect_to_bus(self):
        pass
