import os

from hivemind_bus_client.client import HiveMessageBusClient
from ovos_dinkum_listener.service import OVOSDinkumVoiceService
from ovos_utils.log import LOG
from ovos_config.locale import setup_locale

#: Exit status used when the listener reaches a state it cannot recover from,
#: so a supervisor restarts the satellite instead of leaving it deaf.
UNRECOVERABLE = 1


def on_ready():
    LOG.info('HiveMind Voice Satellite is ready.')


def on_started():
    LOG.info('HiveMind Voice Satellite started.')


def on_alive():
    LOG.info('HiveMind Voice Satellite alive.')


def on_stopping():
    LOG.info('HiveMind Voice Satellite is shutting down...')


def on_error(e='Unknown'):
    """Report an unrecoverable listener failure and end the process.

    ``OVOSDinkumVoiceService.run`` is a thread body. When the voice loop
    raises, it logs, sets the error status and calls ``stop()``, and the
    process stays alive with no thread reading the microphone. The unit
    still looks healthy to systemd, so nothing restarts it and the
    satellite is deaf until a person notices.

    Ending the process is what makes a restart policy work. ``sys.exit``
    would only unwind this thread, so the exit is unconditional.
    """
    LOG.error(f'HiveMind Voice Satellite failed to launch ({e}).')
    LOG.error('exiting so the service manager can restart the satellite')
    os._exit(UNRECOVERABLE)


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

    def _connect_to_bus(self):
        pass
