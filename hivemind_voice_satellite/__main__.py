import click
from hivemind_bus_client import HiveMessageBusClient
from ovos_audio.service import PlaybackService
from ovos_utils import wait_for_exit_signal

from hivemind_voice_satellite import VoiceClient


@click.command(help="connect to HiveMind")
@click.option("--host", help="hivemind host", type=str, default="wss://127.0.0.1")
@click.option("--key", help="Access Key", type=str)
@click.option("--password", help="Password for key derivation", type=str)
@click.option("--port", help="HiveMind port number", type=int, default=5678)
@click.option("--selfsigned", help="accept self signed certificates", is_flag=True)
def connect(host, key, password, port, selfsigned):
    if not host.startswith("ws"):
        print("Invalid host, please specify a protocol")
        print(f"ws://{host} or wss://{host}")
        exit(1)

    # connect to hivemind
    bus = HiveMessageBusClient(key=key,
                               password=password,
                               port=port,
                               host=host,
                               useragent="VoiceSatelliteV0.3.0",
                               self_signed=selfsigned)
    bus.connect()

    # create Audio Output interface (TTS/Music)
    audio = PlaybackService(bus=bus, disable_ocp=True, validate_source=False)
    audio.daemon = True
    audio.start()

    # STT listener thread
    service = VoiceClient(bus=bus)
    service.daemon = True
    service.start()

    wait_for_exit_signal()

    service.stop()
    audio.shutdown()


if __name__ == '__main__':
    connect()
