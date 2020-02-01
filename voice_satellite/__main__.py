from twisted.internet import reactor, ssl
from voice_satellite import JarbasVoiceTerminal, logger, platform
from voice_satellite.configuration import DEFAULT_CONFIG
import base64


def connect_to_hivemind(config=DEFAULT_CONFIG, host="127.0.0.1",
                        port=5678, name="Jarbas Voice Terminal",
                        key="voice_key", useragent=platform):
    authorization = bytes(name + ":" + key, encoding="utf-8")
    usernamePasswordDecoded = authorization
    key = base64.b64encode(usernamePasswordDecoded)

    headers = {'authorization': key}
    address = u"wss://" + host + u":" + str(port)
    logger.info("[INFO] connecting to hive mind at " + address)
    terminal = JarbasVoiceTerminal(config=config, headers=headers,
                                   useragent=useragent)
    contextFactory = ssl.ClientContextFactory()
    reactor.connectSSL(host, port, terminal, contextFactory)
    reactor.run()


if __name__ == '__main__':
    # TODO parse args
    connect_to_hivemind()
