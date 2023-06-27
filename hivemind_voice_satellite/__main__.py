from hivemind_bus_client import HiveMessageBusClient
from hivemind_presence import LocalDiscovery
from ovos_audio.service import PlaybackService
from ovos_utils import wait_for_exit_signal

from hivemind_voice_satellite import VoiceClient


def main(access_key=None,
         host="wss://127.0.0.1",
         port=5678,
         password=None,
         self_signed=False,
         bus=None):
    # connect to hivemind
    if not bus:
        bus = HiveMessageBusClient(key=access_key,
                                   password=password,
                                   port=port,
                                   host=host,
                                   useragent="VoiceSatelliteV0.3.0",
                                   self_signed=self_signed)
        bus.connect()

    # create Audio Output interface (TTS/Music)
    audio = PlaybackService(bus=bus, disable_ocp=True, validate_source=False)
    audio.setDaemon(True)
    audio.start()

    # STT listener thread
    service = VoiceClient(bus=bus)
    service.setDaemon(True)
    service.start()

    wait_for_exit_signal()

    service.shutdown()
    audio.shutdown()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--access-key", help="access key", required=True)
    parser.add_argument("--password", help="password", default=None)
    parser.add_argument("--host", help="HiveMind host")
    parser.add_argument("--port", help="HiveMind port number", default=5678)
    parser.add_argument("--self-signed", help="accept self signed ssl certificates", action="store_true")

    args = parser.parse_args()

    if not args.host:
        print("You did not specify a host to connect")
        scan = input("scan for node and attempt to connect? y/n: ")
        if not scan.lower().startswith("y"):
            print("Scan aborted and host not specified, exiting")
            exit(2)
        scanner = LocalDiscovery()
        for node in scanner.scan():
            print("Found HiveMind node: ", node.address)
            try:
                bus = node.connect(args.access_key, args.crypto_key,
                                   useragent="VoiceSatelliteV0.2.0",
                                   self_signed=args.self_signed)
                scanner.stop()
                main(bus=bus)
            except:
                print("failed to connect!")
        exit(2)
    elif not args.host.startswith("ws"):
        print("Invalid host, please specify a protocol")
        print(f"ws://{args.host} or wss://{args.host}")
        exit(1)

    main(host=args.host,
         port=args.port,
         access_key=args.access_key,
         password=args.password)
