from threading import Thread

from mycroft.client.speech.listener import RecognizerLoop
from mycroft.client.speech.service import SpeechClient
from ovos_utils.log import LOG


class VoiceClient(SpeechClient):
    """mycroft speech client, but bus is replaced with hivemind connection"""
    def __init__(self, bus):
        Thread.__init__(self)
        self.bus = bus

        # Register handlers on internal RecognizerLoop bus (WakeWord/STT)
        self.connect_bus_events()
        self.loop = RecognizerLoop(self.bus)
        self.connect_loop_events()

    def handle_speak(self, event):
        """
        recognizer loop wants to speak.
        i think this never happens (and it should not!!)
        but the api for it is in upstream code, disable it
        """
        pass

    def handle_complete_intent_failure(self, event):
        LOG.info("Failed to find intent.")
        # TODO play some error sound

    def run(self):
        try:
            self.loop.run()
        except KeyboardInterrupt:
            return
        except Exception as e:
            LOG.exception(e)
