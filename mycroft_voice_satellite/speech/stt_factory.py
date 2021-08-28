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
from ovos_plugin_manager.stt import load_stt_plugin



class STTFactory:
    _MAPPINGS = {
        "google": "ovos-stt-plugin-chromium",
        "vosk": "ovos-stt-plugin-vosk"
    }

    @staticmethod
    def create(config):
        """Factory method to create a STT engine based on configuration.

        The configuration file ``mycroft.conf`` contains a ``stt`` section with
        the name of a STT module to be read by this method.

        "stt": {
            "module": <engine_name>
        }
        """
        lang = config.get("lang", "en-us")
        stt_module = config.get('module', 'google')
        stt_config = config.get('stt', {}).get(stt_module, {})
        stt_lang = stt_config.get('lang', lang)
        try:
            if stt_module in STTFactory._MAPPINGS:
                stt_module = STTFactory._MAPPINGS[stt_module]

            clazz = load_stt_plugin(stt_module)
            LOG.info('Loaded plugin {}'.format(stt_module))
            if clazz is None:
                raise ValueError('STT module not found')

            stt = clazz(stt_config)
        except Exception:
            LOG.exception('The STT could not be loaded.')
            raise
        return stt
