from mycroft_voice_satellite import connect_to_hivemind
from mycroft_voice_satellite.configuration import CONFIGURATION


if __name__ == '__main__':
    # TODO argparse
    config = CONFIGURATION
    host = "wss://127.0.0.1"
    port = 5678
    name = "JarbasVoiceTerminal"
    key = "dummy_key"
    crypto_key = None

    connect_to_hivemind(config, host, port, name, key, crypto_key)

