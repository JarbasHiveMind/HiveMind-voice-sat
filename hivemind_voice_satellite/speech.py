import time
from threading import Lock
from hivemind_voice_satellite.config import Configuration
from mycroft_bus_client import Message
from mycroft.tts import TTSFactory
from ovos_utils.signal import check_for_signal
from ovos_utils.log import LOG


class TTSService:
    def __init__(self, bus):
        self.bus = bus
        self._last_stop_signal = 0
        self.lock = Lock()

        self.bus.on('mycroft.stop', self.handle_stop)
        self.bus.on('mycroft.audio.speech.stop', self.handle_stop)
        self.bus.on('speak', self.handle_speak)

        self.tts = TTSFactory.create()
        self.tts.init(self.bus)

    def handle_speak(self, event):
        """Handle "speak" message

        Parse sentences and invoke text to speech service.
        """
        # Get conversation ID
        if event.context and 'ident' in event.context:
            ident = event.context['ident']
        else:
            ident = 'unknown'

        with self.lock:
            utterance = event.data['utterance']
            listen = event.data.get('expect_response', False)
            self.mute_and_speak(utterance, ident, listen)

    def mute_and_speak(self, utterance, ident, listen=False):
        """Mute mic and start speaking the utterance using selected tts backend.

        Args:
            utterance:  The sentence to be spoken
            ident:      Ident tying the utterance to the source query
        """
        LOG.info("Speak: " + utterance)
        try:
            self.tts.execute(utterance, ident, listen)
        except Exception:
            LOG.exception('TTS execution failed.')

    def handle_stop(self, event):
        """Handle stop message.

        Shutdown any speech.
        """
        if check_for_signal("isSpeaking", -1):
            self._last_stop_signal = time.time()
            self.tts.playback.clear()  # Clear here to get instant stop
            self.bus.emit(Message("mycroft.stop.handled", {"by": "TTS"}))

    def shutdown(self):
        """Shutdown the audio service cleanly.

        Stop any playing audio and make sure threads are joined correctly.
        """
        if self.tts:
            self.tts.playback.stop()
            self.tts.playback.join()
