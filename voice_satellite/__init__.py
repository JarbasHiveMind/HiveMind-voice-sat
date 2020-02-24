from voice_satellite.speech.listener import RecognizerLoop
from voice_satellite.configuration import CONFIGURATION
from jarbas_hive_mind.slave.terminal import HiveMindTerminalProtocol, \
    HiveMindTerminal

from jarbas_utils.log import LOG
from jarbas_utils import create_daemon
from jarbas_utils.messagebus import Message

platform = "JarbasVoiceTerminalv0.3"


class JarbasVoiceTerminalProtocol(HiveMindTerminalProtocol):

    def onOpen(self):
        super().onOpen()
        create_daemon(self.factory.start_listening)

    def onClose(self, wasClean, code, reason):
        super().onClose(wasClean, code, reason)
        if "WebSocket connection upgrade failed" in reason:
            utterance = "hive mind refused connection, invalid password"
            self.factory.speak(utterance)
        else:
            self.factory.stop_listening()


class JarbasVoiceTerminal(HiveMindTerminal):
    protocol = JarbasVoiceTerminalProtocol

    def __init__(self, config=CONFIGURATION, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.loop = RecognizerLoop(self.config)
        lang = self.config.get("lang", "en")
        tts = self.config.get("tts", {"module": "google"})["module"]
        tts_config = self.config.get("tts", {}).get(tts, {})
        if tts == "google":
            from voice_satellite.tts.google_tts import GoogleTTS
            self.tts = GoogleTTS(lang, tts_config)
        elif tts == "espeak":
            from voice_satellite.tts.espeak_tts import ESpeak
            self.tts = ESpeak(lang, tts_config)
        elif tts == "mimic":
            from voice_satellite.tts.mimic_tts import Mimic
            self.tts = Mimic(lang, tts_config)
        elif tts == "watson":
            from voice_satellite.tts.ibm_tts import WatsonTTS
            self.tts = WatsonTTS(lang, tts_config)
        elif tts == "yandex":
            from voice_satellite.tts.yandex_tts import YandexTTS
            self.tts = YandexTTS(lang, tts_config)
        elif tts == "spdsay":
            from voice_satellite.tts.spdsay_tts import SpdSay
            self.tts = SpdSay(lang, tts_config)
        elif tts == "mary":
            from voice_satellite.tts.mary_tts import MaryTTS
            self.tts = MaryTTS(lang, tts_config)
        elif tts == "bing":
            from voice_satellite.tts.bing_tts import BingTTS
            self.tts = BingTTS(lang, tts_config)
        elif tts == "fa":
            from voice_satellite.tts.fa_tts import FATTS
            self.tts = FATTS(lang, tts_config)
        else:
            raise ValueError("Unknown TTS engine")

    # Voice Output
    def speak(self, utterance):
        self.tts.execute(utterance)

    # Voice Input
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
                   'destination': "hive_mind"}
        msg = {"data": {"utterances": event['utterances'], "lang": "en-us"},
               "type": "recognizer_loop:utterance",
               "context": context}

        self.send_to_hivemind_bus(msg)

    def handle_unknown(self):
        LOG.info("mycroft.speech.recognition.unknown")

    def handle_hotword(self, event):
        config = self.config.get("listener", {})
        ww = config.get("wake_word", "hey mycroft")
        suw = config.get("stand_up_word", "wake up")
        if event["hotword"] != ww and event["hotword"] != suw:
            LOG.info("Hotword Detected: " + event['hotword'])

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
        self.loop.on('recognizer_loop:utterance',
                     self.handle_utterance)
        self.loop.on('recognizer_loop:record_begin',
                     self.handle_record_begin)
        self.loop.on('recognizer_loop:awoken', self.handle_awoken)
        self.loop.on('recognizer_loop:wakeword', self.handle_wakeword)
        self.loop.on('recognizer_loop:hotword', self.handle_hotword)
        self.loop.on('recognizer_loop:record_end',
                     self.handle_record_end)
        self.loop.run()

    def stop_listening(self):
        self.loop.remove_listener('recognizer_loop:utterance',
                                  self.handle_utterance)
        self.loop.remove_listener('recognizer_loop:record_begin',
                                  self.handle_record_begin)
        self.loop.remove_listener('recognizer_loop:awoken',
                                  self.handle_awoken)
        self.loop.remove_listener('recognizer_loop:wakeword',
                                  self.handle_wakeword)
        self.loop.remove_listener('recognizer_loop:hotword',
                                  self.handle_hotword)
        self.loop.remove_listener('recognizer_loop:record_end',
                                  self.handle_record_end)

    # parsed protocol messages
    def handle_incoming_mycroft(self, message):
        assert isinstance(message, Message)
        if message.msg_type == "speak":
            utterance = message.data["utterance"]
            self.speak(utterance)
        elif message.msg_type == "hive.complete_intent_failure":
            LOG.error("complete intent failure")
            self.speak('I don\'t know how to answer that')
