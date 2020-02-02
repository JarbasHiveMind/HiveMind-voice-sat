from voice_satellite.speech.listener import RecognizerLoop
from voice_satellite.configuration import CONFIGURATION
from jarbas_hive_mind.slave.terminal import HiveMindTerminalProtocol, HiveMindTerminal
import json
from responsive_voice import ResponsiveVoice
from jarbas_utils.log import LOG
from jarbas_utils import create_daemon

platform = "JarbasVoiceTerminalv0.1"


class JarbasVoiceTerminalProtocol(HiveMindTerminalProtocol):

    def onOpen(self):
        super().onOpen()
        create_daemon(self.start_listening)

    def send_message(self, msg):
        msg = json.dumps(msg)
        msg = bytes(msg, encoding="utf-8")
        self.sendMessage(msg, False)

    def handle_record_begin(self):
        LOG.info("Begin Recording...")

    def handle_record_end(self):
        LOG.info("End Recording...")

    def handle_awoken(self):
        """ Forward mycroft.awoken to the messagebus. """
        LOG.info("Listener is now Awake: ")

    def handle_wakeword(self, event):
        LOG.info("Wakeword Detected: " + event['utterance'])

    def handle_utterance(self, event):
        context = {'platform': platform, "source": self.peer,
                   'destinatary': "hive_mind"}
        msg = {"data": {"utterances": event['utterances'], "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": context}

        self.send_message(msg)

    def handle_unknown(self):
        LOG.info("mycroft.speech.recognition.unknown")

    def handle_hotword(self, event):
        config = self.factory.config.get("listener", {})
        ww = config.get("wake_word", "hey mycroft")
        suw = config.get("stand_up_word", "wake up")
        if event["hotword"] != ww and event["hotword"] != suw:
            LOG.info("Hotword Detected: " + event['hotword'])

    def handle_sleep(self):
        self.factory.loop.sleep()

    def handle_wake_up(self, event):
        self.factory.loop.awaken()

    def handle_mic_mute(self, event):
        self.factory.loop.mute()

    def handle_mic_unmute(self, event):
        self.factory.loop.unmute()

    def handle_audio_start(self, event):
        """
            Mute recognizer loop
        """
        self.factory.loop.mute()

    def handle_audio_end(self, event):
        """
            Request unmute, if more sources has requested the mic to be muted
            it will remain muted.
        """
        self.factory.loop.unmute()  # restore

    def handle_stop(self, event):
        """
            Handler for mycroft.stop, i.e. button press
        """
        self.factory.loop.force_unmute()

    def start_listening(self):
        self.factory.loop.on('recognizer_loop:utterance', self.handle_utterance)
        self.factory.loop.on('recognizer_loop:record_begin', self.handle_record_begin)
        self.factory.loop.on('recognizer_loop:awoken', self.handle_awoken)
        self.factory.loop.on('recognizer_loop:wakeword', self.handle_wakeword)
        self.factory.loop.on('recognizer_loop:hotword', self.handle_hotword)
        self.factory.loop.on('recognizer_loop:record_end', self.handle_record_end)
        self.factory.loop.run()

    def stop_listening(self):
        self.factory.loop.remove_listener('recognizer_loop:utterance',
                                  self.handle_utterance)
        self.factory.loop.remove_listener('recognizer_loop:record_begin',
                                  self.handle_record_begin)
        self.factory.loop.remove_listener('recognizer_loop:awoken', self.handle_awoken)
        self.factory.loop.remove_listener('recognizer_loop:wakeword',
                                  self.handle_wakeword)
        self.factory.loop.remove_listener('recognizer_loop:hotword',
                                  self.handle_hotword)
        self.factory.loop.remove_listener('recognizer_loop:record_end',
                                  self.handle_record_end)

    def onMessage(self, payload, isBinary):
        if not isBinary:
            payload = payload.decode("utf-8")
            msg = json.loads(payload)
            if msg.get("type", "") == "speak":
                utterance = msg["data"]["utterance"]
                LOG.info("[OUTPUT] " + utterance)
                self.factory.say(utterance)
            elif msg.get("type", "") == "hive.complete_intent_failure":
                LOG.error("complete intent failure")
        else:
            pass

    def onClose(self, wasClean, code, reason):
        super().onClose(wasClean, code, reason)
        if "WebSocket connection upgrade failed" in reason:
            LOG.error("[ERROR] invalid user:key provided")
            utterance = "hive mind refused connection, invalid password"
            self.factory.engine.say(utterance)
        else:
            self.stop_listening()


class JarbasVoiceTerminal(HiveMindTerminal):
    protocol = JarbasVoiceTerminalProtocol

    def __init__(self, config=CONFIGURATION, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.play_cmd = "mpg123 -q %1"
        self.engine = ResponsiveVoice(gender="female")
        self.config = config
        self.loop = RecognizerLoop(self.config)

    def say(self, utterance):
        self.engine.say(utterance, play_cmd=self.play_cmd)
