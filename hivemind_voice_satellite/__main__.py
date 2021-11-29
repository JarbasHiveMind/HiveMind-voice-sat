from mycroft.configuration import setup_locale
from mycroft.util import wait_for_exit_signal
from mycroft.util.log import LOG

from hivemind_bus_client import HiveMessageBusClient
from hivemind_voice_satellite import VoiceClient, TTSService, AudioService


def main(access_key,
         host="wss://127.0.0.1",
         port=5678,
         crypto_key=None):

    # timezone/lang preferences from .conf
    setup_locale()

    # connect to hivemind
    bus = HiveMessageBusClient(key=access_key,
                               crypto_key=crypto_key,
                               port=port,
                               host=host,
                               ssl=host.startswith("wss:"),
                               useragent="VoiceSatelliteV0.2.0",
                               self_signed=True, debug=True)
    bus.run_in_thread()

    # block until hivemind connects
    LOG.info("Waiting for Hivemind connection")
    bus.connected_event.wait()

    # create Audio Output interface (Music)
    audio = AudioService(bus)

    # Initialize TTS
    tts = TTSService(bus)

    # STT listener thread
    service = VoiceClient(bus)
    service.setDaemon(True)
    service.start()

    wait_for_exit_signal()

    tts.shutdown()
    audio.shutdown()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--access_key", help="access key")
    parser.add_argument("--crypto_key", help="payload encryption key", default=None)
    parser.add_argument("--host", help="HiveMind host", default="wss://127.0.0.1")
    parser.add_argument("--port", help="HiveMind port number", default=5678)

    args = parser.parse_args()

    main(host=args.host,
         port=args.port,
         access_key=args.access_key,
         crypto_key=args.crypto_key)

