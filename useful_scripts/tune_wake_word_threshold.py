"""
Script for auto tuning keyword spotting thresholds in pocketsphinx.
"""
import os
import time
import tempfile

import pickle

from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *
from speech_recognition import Microphone

# Load/Save configuration
bool_load = False
bool_save = False
audio_dir = os.path.join('.', 'wakedump')
# Define hotword (the threshold for detection needs to be low)
"""
hotword = {
    "name": "hey mycroft",
    "phonemes": "HH EY . M AY K R AO F T",
    "lang": "en-us",
    "threshold": 1e-90,
}
"""
hotword = {
    "name": "escucha paco",
    "phonemes": "e s k u ch a . p a k o",
    "lang": "es-es",
    "threshold": 1e-90,
}
# Model dir
modeldir = os.path.join('.', 'mycroft_voice_satellite', 'speech', 'recognizer', 'model', hotword['lang'], 'hmm')
# Sampling rate
sample_rate=16000

# Create file for sphinx
(fd, file_name) = tempfile.mkstemp()
words = hotword['name'].split()
phoneme_groups = hotword['phonemes'].split('.')
with os.fdopen(fd, 'w') as f:
    for word, phoneme in zip(words, phoneme_groups):
        f.write(word + ' ' + phoneme + '\n')

# sphinx hotword engine
def hotword_engine(threshold):
    config = Decoder.default_config()
    config.set_string('-hmm', modeldir)
    config.set_string('-dict', file_name)
    config.set_string('-keyphrase', hotword['name'])
    config.set_float('-kws_threshold', float(threshold))
    config.set_float('-samprate', sample_rate)
    config.set_int('-nfft', 2048)
    if os.name == 'nt': config.set_string('-logfn', 'NUL')
    else: config.set_string('-logfn', '/dev/null')
    config.set_string('-featparams', os.path.join(modeldir, "feat.params"))
    return Decoder(config)

if bool_load:
    audio_samples = pickle.load(open(audio_dir, "rb"))
    N_realizations = len(audio_samples)
else:
    # Create sphinx model for detecting hotwords
    hwe = hotword_engine(hotword['threshold'])
    # Define Microphone
    mic = Microphone(device_index=None, sample_rate=sample_rate, chunk_size=1024)
    # Record hotword
    N_realizations = 5
    audio_samples = []
    for realization in range(N_realizations):
        sample = b''
        if realization > 0: time.sleep(0.5)
        with mic as source:
            hyp = False
            sample += source.stream.read(source.CHUNK)
            print('say "{}" {}/{} ... '.format(hotword['name'], realization+1, N_realizations))
            while not hyp:
                # Capture
                chunk = source.stream.read(source.CHUNK)
                sample += chunk
                # Find hotword
                hwe.start_utt()
                hwe.process_raw(sample, False, False)
                hwe.end_utt()
                hyp = hwe.hyp()
        audio_samples.append(sample)
        print('detected')
    if bool_save:
        pickle.dump(audio_samples, open(audio_dir, "wb"))

# Found hotword function
def found_hotwork(hwe, sample):
    hwe.start_utt()
    hwe.process_raw(sample, False, False)
    hwe.end_utt()
    return hwe.hyp() is not None

# Find maximum threshold for which all samples are detected
# Refine B
detected = [False for sample in audio_samples]
for nthreshold_B in range(50):
    threshold = pow(10, -nthreshold_B)
    hwe = hotword_engine(threshold)
    print('detected')
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    print(detected)
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    print(detected)
    nthr_B = nthreshold_B
    if all(detected):
        break
# Refine dB
detected = [False for sample in audio_samples]
for nthreshold_dB in range(10*nthr_B-10, 10*nthr_B):
    threshold = pow(10, -nthreshold_dB/10)
    hwe = hotword_engine(threshold)
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    nthr_dB = nthreshold_dB
    if all(detected):
        break
# Refine cB
detected = [False for sample in audio_samples]
for nthreshold_cB in range(10*nthr_dB-10, 10*nthr_dB):
    threshold = pow(10, -nthreshold_cB/100)
    hwe = hotword_engine(threshold)
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    detected = [found_hotwork(hwe, sample) for sample in audio_samples]
    nthr_cB = nthreshold_cB
    if all(detected):
        break
# Print result
threshold = pow(10, -nthr_cB/100)
print('threshold: {:5e}'.format(threshold))
