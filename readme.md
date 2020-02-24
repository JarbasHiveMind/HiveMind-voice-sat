# HiveMind Voice Satellite

Mycroft Voice Satellite, connect to [HiveMind-core](https://github.com/OpenJarbas/HiveMind-core)

- [HiveMind Voice Satellite](#hivemind-voice-satellite)
  * [Setup](#setup)
    + [Install](#install)
    + [Usage](#usage)
    + [Configuration](#configuration)
      - [configure speech to text](#configure-speech-to-text)
      - [configure text to speech](#configure-text-to-speech)
      - [Configure hotwords](#configure-hotwords)
      - [configure listener](#configure-listener)


![](./voice_sat.png)

## Setup

### Install

```bash
pip install git+https://github.com/OpenJarbas/HiveMind-voice-sat
```

### Usage

```python

from voice_satellite.configuration import CONFIGURATION
from voice_satellite import JarbasVoiceTerminal, platform
from jarbas_hive_mind import HiveMindConnection


def connect_to_hivemind(config=CONFIGURATION, host="wss://127.0.0.1",
                        port=5678, name="JarbasVoiceTerminal",
                        key="dummy_key", crypto_key=None,

                        useragent=platform):
                        
    # key is the authentication key registered in hivemind-core
    # crypto_key is used to de/encrypt all messages and must match crypto-key stored in hivemind-core
    # name is a currently placeholder nickname and not used for authentication
    con = HiveMindConnection(host, port)

    terminal = JarbasVoiceTerminal(config=config,
                                   crypto_key=crypto_key,
                                   headers=con.get_headers(name, key),
                                   useragent=useragent)

    con.connect(terminal)

```
### Configuration

You can set the configuration at
    
    ~/.jarbasHiveMind/voice_sat.conf
    
Otherwise default configuration will be used, check bellow for defaults

#### configure speech to text
```json
{
    "lang": "en-us",
    "stt": {
        "module": "google",
        "deepspeech_server": {
            "uri": "http://localhost:8080/stt"
        },
        "kaldi": {
            "uri": "http://localhost:8080/client/dynamic/recognize"
        }
    }
}
```

#### configure text to speech
```json
{
    "lang": "en-us",
    "tts": {
        "module": "google"
    }
}
```

#### Configure hotwords

add any number of hot words to config
- hot word can be any engine (snowboy/pocketsphinx/precise)
- hot word can trigger listening or not
- hot word can play a sound or not
- hot word can be treated as full utterance or not

```json
{
    "hotwords": {
        "hey mycroft": {
            "module": "pocketsphinx",
            "phonemes": "HH EY . M AY K R AO F T",
            "threshold": 1e-90,
            "lang": "en-us",
            "sound": "snd/start_listening.wav",
            "listen": true
        },
        "thank you": {
            "module": "pocketsphinx",
            "phonemes": "TH AE NG K . Y UW .",
            "threshold": 0.1,
            "listen": false,
            "utterance": "thank you",
            "active": false,
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
}
```

#### configure listener

```json
{
    "data_dir": "~/jarbasHiveMind/recordings",
    "listener": {
        "sample_rate": 16000,
        "channels": 1,
        "record_wake_words": false,
        "record_utterances": false,
        "phoneme_duration": 120,
        "multiplier": 1.0,
        "energy_ratio": 1.5,
        "stand_up_word": "wake up"
    }
}
```
data_dir is where recordings are saved, 

    {data_dir}/utterances
    {data_dir}/hotwords

you can optionally set device_index
```json
{
    "listener": {
        "device_index": 0
    }
}
```  
or device_name, which is a name or regex pattern
```json
{
    "listener": {
        "device_name": "respeaker"
    }
}
```  