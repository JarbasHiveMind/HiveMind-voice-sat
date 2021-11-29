from threading import Thread

from mycroft.client.speech.listener import RecognizerLoop
from mycroft.client.speech.service import SpeechClient
from mycroft.util.process_utils import ProcessStatus, StatusCallbackMap
from ovos_utils.log import LOG


def on_ready():
    LOG.info('Speech client is ready.')


def on_stopping():
    LOG.info('Speech service is shutting down...')


def on_error(e='Unknown'):
    LOG.error(f'Speech service failed to launch ({e}).')


class VoiceClient(SpeechClient):
    """mycroft speech client, but bus is replaced with hivemind connection"""

    def __init__(self, bus, on_ready=on_ready, on_error=on_error,
                 on_stopping=on_stopping, watchdog=lambda: None):
        Thread.__init__(self)
        self.bus = bus

        # watchdog
        callbacks = StatusCallbackMap(on_ready=on_ready,
                                      on_error=on_error,
                                      on_stopping=on_stopping)
        self.status = ProcessStatus('speech', callback_map=callbacks)
        self.status.set_started()
        self.status.bind(self.bus)

        # Register handlers on internal RecognizerLoop bus (WakeWord/STT)
        self.connect_bus_events()
        self.loop = RecognizerLoop(self.bus, watchdog)
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
