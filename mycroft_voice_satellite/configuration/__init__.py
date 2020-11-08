from json_database import JsonStorageXDG
from os.path import exists, expanduser, join
from tempfile import gettempdir

DEFAULT_CONFIGURATION = {
    'data_dir': expanduser('~/jarbasHiveMind/recordings'),
    'host': '0.0.0.0',
    'port': 5678,
    'hotwords': {'hey mycroft': {'lang': 'en-us',
                                 'listen': True,
                                 'module': 'pocketsphinx',
                                 'phonemes': 'HH EY . M AY K R AO F T',
                                 'sound': 'snd/start_listening.wav',
                                 'threshold': 1e-90},
                 'thank you': {'active': False,
                               'lang': 'en-us',
                               'listen': False,
                               'module': 'pocketsphinx',
                               'phonemes': 'TH AE NG K . Y UW .',
                               'sound': '',
                               'threshold': 0.1,
                               'utterance': 'thank you'},
                 'wake up': {'lang': 'en-us',
                             'module': 'pocketsphinx',
                             'phonemes': 'W EY K . AH P',
                             'threshold': 1e-20}},
    'lang': 'en-us',
    'listener': {'channels': 1,
                 'energy_ratio': 1.5,
                 'multiplier': 1.0,
                 'phoneme_duration': 120,
                 'record_utterances': False,
                 'record_wake_words': False,
                 'sample_rate': 16000,
                 'stand_up_word': 'wake up',
                 'signal_folder': join(gettempdir(), "hivemind", "ipc"),
                 'listen_sound': 'snd/start_listening.wav',
                 'error_sound': 'snd/listening_error.mp3'},
    'stt': {'deepspeech_server': {'uri': 'http://localhost:8080/stt'},
            'deepspeech_stream_server': {
                'stream_uri': 'http://localhost:8080/stt?format=16K_PCM16'},
            'kaldi': {
                'uri': 'http://localhost:8080/client/dynamic/recognize'},
            'kaldi_vosk': {'model': '/path/to/model/folder'},
            'kaldi_vosk_streaming': {'model': '/path/to/model/folder'},
            "deepspeech": {"model": "path/to/model.pbmm",
                           "scorer": "path/to/model.scorer"},
            "deepspeech_streaming": {"model": "path/to/model.pbmm",
                                     "scorer": "path/to/model.scorer"},
            'module': 'google'},
    'tts': {'module': 'responsive_voice'},
    'playback': {
        'play_wav_cmd': "aplay %1",
        'play_mp3_cmd': "mpg123 %1",
        'play_ogg_cmd': "ogg123 -q %1",
        'play_fallback_cmd': "play %1"
    },
    'log_blacklist': []
}


def _merge_defaults(base, default=None):
    """
        Recursively merging configuration dictionaries.

        Args:
            base:  Target for merge
            default: Dictionary to merge into base if key not present
    """
    default = default or DEFAULT_CONFIGURATION
    for k, dv in default.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            _merge_defaults(bv, dv)
        elif k not in base:
            base[k] = dv
    return base


CONFIGURATION = JsonStorageXDG("HivemindVoiceSatellite")
CONFIGURATION = _merge_defaults(CONFIGURATION)
if not exists(CONFIGURATION.path):
    CONFIGURATION.store()
