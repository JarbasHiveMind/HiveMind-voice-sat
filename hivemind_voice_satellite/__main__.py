from threading import Event

import click
from hivemind_bus_client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from hivemind_ggwave import GGWaveSlave
from ovos_audio.service import PlaybackService
from ovos_bus_client.client import MessageBusClient
from ovos_utils import wait_for_exit_signal
from ovos_utils.log import init_service_logger, LOG
from ovos_utils.fakebus import FakeBus
from hivemind_voice_satellite import VoiceClient


def launch_bus_daemon() -> MessageBusClient:
    from ovos_utils import create_daemon
    from tornado import web, ioloop
    from ovos_messagebus.event_handler import MessageBusEventHandler

    INTERNAL_PORT = 9987  # can be anything, wanted to differentiate from standard ovos-bus

    routes = [("/core", MessageBusEventHandler)]
    application = web.Application(routes)
    application.listen(INTERNAL_PORT, "127.0.0.1")
    create_daemon(ioloop.IOLoop.instance().start)

    bus = MessageBusClient(host="127.0.0.1", port=INTERNAL_PORT)
    bus.run_in_thread()
    return bus


# TODO - add a flag to use FakeBus instead of real websocket
@click.command(help="connect to HiveMind")
@click.option("--host", help="hivemind host", type=str, default="")
@click.option("--key", help="Access Key", type=str, default="")
@click.option("--password", help="Password for key derivation", type=str, default="")
@click.option("--port", help="HiveMind port number", type=int, default=5678)
@click.option("--selfsigned", help="accept self signed certificates", is_flag=True)
@click.option("--siteid", help="location identifier for message.context", type=str, default="")
def connect(host, key, password, port, selfsigned, siteid):
    init_service_logger("HiveMind-voice-sat")

    identity = NodeIdentity()
    password = password or identity.password
    key = key or identity.access_key
    siteid = siteid or identity.site_id or "unknown"
    host = host or identity.default_master

    if not password:
        LOG.info("starting hivemind-ggwave, waiting for audio password")
        try:

            ggwave = GGWaveSlave(key=key)  # reuse existing key

            ready = Event()

            def handle_complete(message):
                nonlocal identity, password, key, host, ready
                identity.reload()
                password = identity.password
                host = identity.default_master
                key = identity.access_key
                LOG.info(f"will connect to: {host}")
                ready.set()

            ggwave.bus.on("hm.ggwave.identity_updated",
                          handle_complete)
            ggwave.start()

            ready.wait()

            ggwave.stop()

        except Exception as e:
            LOG.exception("hivemind-ggwave failed to start")

    if not key or not password or not host:
        raise RuntimeError("NodeIdentity not set, please pass key/password/host or "
                           "call 'hivemind-client set-identity'")

    if not host.startswith("ws://") and not host.startswith("wss://"):
        host = "ws://" + host

    if not host.startswith("ws"):
        LOG.error("Invalid host, please specify a protocol")
        LOG.error(f"ws://{host} or wss://{host}")
        exit(1)

    # TODO - flag for fakebus
    internal_bus = launch_bus_daemon() or FakeBus()

    # connect to hivemind
    bus = HiveMessageBusClient(key=key,
                               password=password,
                               port=port,
                               host=host,
                               useragent="VoiceSatelliteV0.3.1",
                               self_signed=selfsigned,
                               internal_bus=internal_bus)
    bus.connect(site_id=siteid)

    # create Audio Output interface (TTS/Music)
    audio = PlaybackService(bus=bus, validate_source=False)
    audio.daemon = True
    audio.start()

    # STT listener thread
    service = VoiceClient(bus=bus)
    service.daemon = True
    service.start()

    try:
        from ovos_PHAL.service import PHAL
        phal = PHAL(bus=bus)
        phal.start()
    except ImportError:
        print("PHAL is not available")
        phal = None

    wait_for_exit_signal()

    service.stop()
    audio.shutdown()
    if phal:
        phal.shutdown()


if __name__ == '__main__':
    connect()
