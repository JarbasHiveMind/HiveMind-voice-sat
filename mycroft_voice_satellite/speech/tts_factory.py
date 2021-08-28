# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from time import time, sleep
import os
import platform
import posixpath
import tempfile
import requests
from contextlib import suppress
from glob import glob
from os.path import dirname, exists, join, abspath, expanduser, isfile, isdir
from shutil import rmtree
from threading import Timer, Event, Thread
from urllib.error import HTTPError

from mycroft_voice_satellite.configuration import CONFIGURATION
from ovos_utils.log import LOG
from ovos_plugin_manager.tts import load_tts_plugin



class TTSFactory:
    """Factory class instantiating the configured TTS engine.

    The factory can select between a range of built-in TTS engines and also
    from TTS engine plugins.
    """
    _MAPPINGS = {
        "mimic": "ovos-tts-plugin-mimic",
        "mimic2": "ovos-tts-plugin-mimic2",
        "google": "ovos-tts-plugin-google-tx",
        "pico":  "ovos-tts-plugin-pico",
        "espeak":  "ovos-tts-plugin-espeakNG",
        "responsive_voice": "ovos-tts-plugin-responsivevoice",
        "polly": "chatterbox-polly-tts-plugin"
    }

    @staticmethod
    def create(config):
        """Factory method to create a TTS engine based on configuration.

        The configuration file ``mycroft.conf`` contains a ``tts`` section with
        the name of a TTS module to be read by this method.

        "tts": {
            "module": <engine_name>
        }
        """
        lang = config.get("lang", "en-us")
        tts_module = config.get('module', 'responsive_voice')
        tts_config = config.get('tts', {}).get(tts_module, {})
        tts_lang = tts_config.get('lang', lang)
        try:
            if tts_module in TTSFactory._MAPPINGS:
                tts_module = TTSFactory._MAPPINGS[tts_module]

            clazz = load_tts_plugin(tts_module)
            LOG.info('Loaded plugin {}'.format(tts_module))
            if clazz is None:
                raise ValueError('TTS module not found')

            tts = clazz(lang=tts_lang, config=tts_config)
            tts.validator.validate()
        except Exception:
            LOG.exception('The TTS could not be loaded.')
            raise
        return tts
