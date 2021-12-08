import json
import os
from os.path import join, isfile

import xdg.BaseDirectory
from json_database import JsonStorage, JsonStorageXDG
from ovos_utils.json_helper import merge_dict
from ovos_utils.log import LOG


def setup_ovos_core_config():
    """
    Runs at module init to ensure base ovos.conf exists to patch ovos-core.
    Note that this must run before any import of mycroft Configuration class.
    """
    OVOS_CONFIG = join(xdg.BaseDirectory.save_config_path("OpenVoiceOS"),
                       "ovos.conf")

    _HIVEMIND_OVOS_CONFIG = {
        "module_overrides": {
            "hivemind": {
                "xdg": True,
                "base_folder": "hivemind",
                "config_filename": "hivemind.conf"
            }
        },
        # if these services are running standalone
        # config them to use hivemind config from above
        "submodule_mappings": {
            "hivemind_voice_satellite": "hivemind"
        }
    }

    cfg = {}
    try:
        with open(OVOS_CONFIG) as f:
            cfg = json.load(f)
    except FileNotFoundError:
        pass
    except Exception as e:
        LOG.error(e)

    cfg = merge_dict(cfg, _HIVEMIND_OVOS_CONFIG)
    with open(OVOS_CONFIG, "w") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=True)

    hivemind_cfg = JsonStorage(f'{xdg.BaseDirectory.save_config_path("hivemind")}/hivemind.conf')

    # migrate old config location
    old_cfg = JsonStorageXDG("HivemindVoiceSatellite")
    if isfile(old_cfg.path):
        LOG.warning(f"You have a config file in {old_cfg.path}\n"
                    f"This location has been deprecated, use {hivemind_cfg.path} instead\n"
                    f"Your old config file will be automatically migrated and deleted from the old location!")
        hivemind_cfg.update({k: v for k, v in old_cfg.items()
                             if k not in hivemind_cfg})
        os.remove(old_cfg.path)

    # populate default config values
    default_cfg = {
        "lang": "en-us",
        "stt": {
            "module": "google"
        },
        "tts": {
            "module": "mimic2"
        },
        "hotwords": {
            "hey mycroft": {
                "module": "pocketsphinx",
                "phonemes": "HH EY . M AY K R AO F T",
                "threshold": 1e-90,
                "lang": "en-us",
                "sound": "snd/start_listening.wav",
                "listen": True
            },
            "wake up": {
                "module": "pocketsphinx",
                "phonemes": "W EY K . AH P",
                "threshold": 1e-20,
                "lang": "en-us"
            }
        }
    }
    default_cfg = {k: v for k, v in default_cfg.items() if k not in hivemind_cfg}
    hivemind_cfg.update(default_cfg)

    # create config file if it doesnt exist
    if not isfile(hivemind_cfg.path):
        hivemind_cfg.store()
    return hivemind_cfg


HivemindConfiguration = setup_ovos_core_config()

from mycroft.configuration import Configuration
from mycroft.configuration import setup_locale
