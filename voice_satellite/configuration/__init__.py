from json_database import JsonStorage
from os.path import expanduser, exists

_DEFAULT_CONFIG_PATH = expanduser("~/.jarbasHiveMind/voice_sat.conf")


def default_config():
    default = JsonStorage(_DEFAULT_CONFIG_PATH)

    default["host"] = "0.0.0.0"
    default["port"] = 5678
    default["stt"] = {
        "module": "google",
        "deepspeech_server": {
            "uri": "http://localhost:8080/stt"
        },
        "kaldi": {
            "uri": "http://localhost:8080/client/dynamic/recognize"
        }
    }
    default["listener"] = {
        "sample_rate": 16000,
        "channels": 1,
        "record_wake_words": False,
        "record_utterances": False,
        "phoneme_duration": 120,
        "multiplier": 1.0,
        "energy_ratio": 1.5,
        "wake_word": "hey mycroft",
        "stand_up_word": "wake up"
    }
    default["hotwords"] = {
        "hey mycroft": {
            "module": "pocketsphinx",
            "phonemes": "HH EY . M AY K R AO F T",
            "threshold": 1e-90,
            "lang": "en-us"
        },
        "thank you": {
            "module": "pocketsphinx",
            "phonemes": "TH AE NG K . Y UW .",
            "threshold": 1e-1,
            "listen": False,
            "utterance": "thank you",
            "active": False,
            "sound": "",
            "lang": "en-us"
        },
        "wake up": {
            "module": "pocketsphinx",
            "phonemes": "W EY K . AH P",
            "threshold": 1e-20,
            "lang": "en-us"
        }
    }
    default["log_blacklist"] = []
    return default


if not exists(_DEFAULT_CONFIG_PATH):
    CONFIGURATION = default_config()
    CONFIGURATION.store()
else:
    CONFIGURATION = JsonStorage(_DEFAULT_CONFIG_PATH)
