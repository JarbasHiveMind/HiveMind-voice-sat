from json_database import JsonStorage
from os.path import expanduser, exists


_DEFAULT_CONFIG_PATH = expanduser("~/.jarbasHiveMind/voice_sat.conf")


def get_default_config():
    default = JsonStorage(_DEFAULT_CONFIG_PATH)
    default["lang"] = "en-us"
    default["host"] = "0.0.0.0"
    default["port"] = 5678
    default["data_dir"] = "~/jarbasHiveMind/recordings"
    default["tts"] = {
        "module": "responsive_voice"
    }
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
        "stand_up_word": "wake up"
    }
    default["hotwords"] = {
        "hey mycroft": {
            "module": "pocketsphinx",
            "phonemes": "HH EY . M AY K R AO F T",
            "threshold": 1e-90,
            "lang": "en-us",
            "sound": "snd/start_listening.wav",
            "listen": True
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


DEFAULT_CONFIGURATION = get_default_config()


def merge_dict(base, delta):
    """
        Recursively merging configuration dictionaries.

        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
    """

    for k, dv in delta.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            merge_dict(bv, dv)
        else:
            base[k] = dv
    return base


CONFIGURATION = JsonStorage(_DEFAULT_CONFIG_PATH)
CONFIGURATION = merge_dict(DEFAULT_CONFIGURATION, CONFIGURATION)
