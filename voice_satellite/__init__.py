from threading import Thread

from autobahn.twisted.websocket import WebSocketClientFactory, \
    WebSocketClientProtocol
from twisted.internet.protocol import ReconnectingClientFactory

from voice_satellite.speech.listener import RecognizerLoop
from voice_satellite.configuration import DEFAULT_CONFIG

import json
import sys
import logging
from responsive_voice import ResponsiveVoice

platform = "JarbasVoiceTerminalv0.1"

logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class JarbasVoiceTerminalProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        logger.info("[INFO] Server connected: {0}".format(response.peer))
        self.factory.client = self
        self.factory.status = "connected"

    def onOpen(self):
        logger.info("[INFO] WebSocket connection open. ")
        self.loop = RecognizerLoop(self.factory.config)
        self.listen = Thread(target=self.start_listening)
        self.listen.setDaemon(True)
        self.listen.start()

    def handle_record_begin(self):
        logger.info("[INFO] Begin Recording...")

    def handle_record_end(self):
        logger.info("[INFO] End Recording...")

    def handle_awoken(self):
        """ Forward mycroft.awoken to the messagebus. """
        logger.info("[INFO] Listener is now Awake: ")

    def handle_wakeword(self, event):
        logger.info("[INFO] Wakeword Detected: " + event['utterance'])

    def handle_utterance(self, event):
        context = {'platform': platform, "source": self.peer,
                   'destinatary': "hive_mind"}
        msg = {"data": {"utterances": event['utterances'], "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": context}

        self.send(msg)

    def handle_unknown(self):
        logger.info("[INFO] mycroft.speech.recognition.unknown")

    def handle_hotword(self, event):
        config = self.factory.config.get("listener", {})
        ww = config.get("wake_word", "hey mycroft")
        suw = config.get("stand_up_word", "wake up")
        if event["hotword"] != ww and event["hotword"] != suw:
            logger.info("[INFO] Hotword Detected: " + event['hotword'])

    def handle_sleep(self):
        self.loop.sleep()

    def handle_wake_up(self, event):
        self.loop.awaken()

    def handle_mic_mute(self, event):
        self.loop.mute()

    def handle_mic_unmute(self, event):
        self.loop.unmute()

    def handle_audio_start(self, event):
        """
            Mute recognizer loop
        """
        self.loop.mute()

    def handle_audio_end(self, event):
        """
            Request unmute, if more sources has requested the mic to be muted
            it will remain muted.
        """
        self.loop.unmute()  # restore

    def handle_stop(self, event):
        """
            Handler for mycroft.stop, i.e. button press
        """
        self.loop.force_unmute()

    def start_listening(self):
        self.loop.on('recognizer_loop:utterance', self.handle_utterance)
        self.loop.on('recognizer_loop:record_begin', self.handle_record_begin)
        self.loop.on('recognizer_loop:awoken', self.handle_awoken)
        self.loop.on('recognizer_loop:wakeword', self.handle_wakeword)
        self.loop.on('recognizer_loop:hotword', self.handle_hotword)
        self.loop.on('recognizer_loop:record_end', self.handle_record_end)
        self.loop.run()

    def stop_listening(self):
        self.loop.remove_listener('recognizer_loop:utterance',
                                  self.handle_utterance)
        self.loop.remove_listener('recognizer_loop:record_begin',
                                  self.handle_record_begin)
        self.loop.remove_listener('recognizer_loop:awoken', self.handle_awoken)
        self.loop.remove_listener('recognizer_loop:wakeword',
                                  self.handle_wakeword)
        self.loop.remove_listener('recognizer_loop:hotword',
                                  self.handle_hotword)
        self.loop.remove_listener('recognizer_loop:record_end',
                                  self.handle_record_end)
        self.listen.join(0)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                logger.info("[OUTPUT] " + utterance)
                self.factory.engine.say(utterance)
            elif msg.get("type", "") == "hive.complete_intent_failure":
                logger.error("[ERROR] complete intent failure")
        else:
            pass

    def send(self, msg):
        msg = json.dumps(msg)
        msg = bytes(msg, encoding="utf-8")
        self.sendMessage(msg, False)

    def onClose(self, wasClean, code, reason):
        logger.info(
            "[INFO] WebSocket connection closed: {0}".format(reason))
        self.stop_listening()
        self.factory.client = None
        self.factory.status = "disconnected"
        if "Internalservererror:InvalidAPIkey" in reason:
            logger.error("[ERROR] invalid user:key provided")
            utterance = "hive mind refused connection, invalid user or key " \
                        "provided"
            self.factory.engine.say(utterance)
            raise ConnectionAbortedError("invalid user:key provided")


class JarbasVoiceTerminal(WebSocketClientFactory,
                          ReconnectingClientFactory):
    protocol = JarbasVoiceTerminalProtocol

    def __init__(self, config=DEFAULT_CONFIG, *args, **kwargs):
        super(JarbasVoiceTerminal, self).__init__(*args, **kwargs)
        self.status = "disconnected"
        self.client = None
        # TODO make optional
        self.engine = ResponsiveVoice(gender="female")
        self.config = config

    # websocket handlers
    def clientConnectionFailed(self, connector, reason):
        logger.info("[INFO] Client connection failed: " +
                    str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)

    def clientConnectionLost(self, connector, reason):
        logger.info("[INFO] Client connection lost: " +
                    str(reason) + " .. retrying ..")
        self.status = "disconnected"
        self.retry(connector)
