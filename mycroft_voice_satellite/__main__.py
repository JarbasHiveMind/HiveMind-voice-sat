from mycroft_voice_satellite import connect_to_hivemind, JarbasVoiceTerminal
from jarbas_hive_mind import HiveMindConnection
from jarbas_hive_mind.discovery import LocalDiscovery
from jarbas_utils.log import LOG
from time import sleep

def discover_hivemind(name="JarbasVoiceTerminal",
                      access_key="RESISTENCEisFUTILE",
                      crypto_key="resistanceISfutile"):
    discovery = LocalDiscovery()
    headers = HiveMindConnection.get_headers(name, access_key)

    while True:
        print("Scanning...")
        for node_url in discovery.scan():
            LOG.info("Fetching Node data: {url}".format(url=node_url))
            node = discovery.nodes[node_url]
            node.connect(crypto_key=crypto_key,
                         node_type=JarbasVoiceTerminal,
                         headers=headers
                         )
        sleep(5)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--access_key", help="access key",
                        default="RESISTENCEisFUTILE")
    parser.add_argument("--crypto_key", help="payload encryption key",
                        default="resistanceISfutile")
    parser.add_argument("--name", help="human readable device name",
                        default="JarbasVoiceTerminal")
    parser.add_argument("--host", help="HiveMind host")
    parser.add_argument("--port", help="HiveMind port number", default=5678)

    args = parser.parse_args()

    if args.host:
        # Direct Connection
        connect_to_hivemind(args.host, args.port,
                            args.name, args.access_key, args.crypto_key)

    else:
        # Auto discovery
        discover_hivemind(args.name, args.access_key, args.crypto_key)


if __name__ == '__main__':
    main()
