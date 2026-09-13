from hivemind_bus_client.client import HiveMessageBusClient
from ovos_dinkum_listener.service import OVOSDinkumVoiceService
from ovos_utils.log import LOG
from ovos_config import Configuration
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


def _keep_configuration_sync_local(bus: HiveMessageBusClient):
    """Bind ovos_config's change sync to the satellite's own internal bus.

    Every ``Configuration()[key] = value`` emits ``configuration.patch`` on
    ``Configuration.bus`` to keep other local processes in sync. ovos-audio
    binds that to the HiveMind client, so the patch was sent to the hub: the
    hub denied it, and before the client ran it raised ValueError. A
    satellite's services share one process, so there is nothing to sync over
    the hive, and a satellite must not patch the hub's configuration.

    Handlers stay where they were: the client registers them on
    ``internal_bus`` anyway, and a ``configuration.patch`` the hub sends
    down still arrives there. Only the emit stops leaving the device.
    """
    internal = getattr(bus, "internal_bus", None)
    if internal is not None and Configuration.bus is not internal:
        Configuration.set_config_update_handlers(internal)


class VoiceClient(OVOSDinkumVoiceService):
    """HiveMind Voice Satellite, but bus is replaced with hivemind connection"""

    def __init__(self, bus: HiveMessageBusClient, on_ready=on_ready, on_error=on_error,
                 on_stopping=on_stopping, on_alive=on_alive,
                 on_started=on_started, watchdog=lambda: None, mic=None, **kwargs):
        _keep_configuration_sync_local(bus)
        setup_locale()  # read mycroft.conf for default lang/timezone in all modules (eg, lingua_franca)
        # **kwargs is forwarded to OVOSDinkumVoiceService so callers may inject
        # stt / vad / hotwords (e.g. tests passing in-process fakes).
        super().__init__(on_ready, on_error, on_stopping, on_alive, on_started, watchdog, mic,
                         bus=bus, validate_source=False, **kwargs)

    def _connect_to_bus(self):
        pass
