
from mycroft.audio.audioservice import AudioService
from mycroft.configuration import setup_locale
from mycroft.util import wait_for_exit_signal
from mycroft.util.log import LOG

from hivemind_bus_client import HiveMessageBusClient
from hivemind_voice_satellite.service import VoiceClient
from hivemind_voice_satellite.speech import TTSService


def main():
    # timezone/lang preferences from .conf
    setup_locale()

    # connect to hivemind
    key = "RESISTENCEisFUTILE"
    crypto_key = "resistanceISfutile"

    bus = HiveMessageBusClient(key, crypto_key=crypto_key, ssl=True,
                               useragent="VoiceSatelliteV0.2.0",
                               self_signed=True, debug=False)

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


if __name__ == "__main__":
    main()
