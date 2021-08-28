from setuptools import setup

setup(
    name='HiveMind-voice-sat',
    version='1.0.7',
    packages=['mycroft_voice_satellite', 'mycroft_voice_satellite.speech',
              'mycroft_voice_satellite.res',
              'mycroft_voice_satellite.configuration'],
    install_requires=["jarbas_hive_mind",
                      "SpeechRecognition @ git+https://github.com/Uberi/speech_recognition.git",
                      "pyee",
                      "requests",
                      "requests_futures",
                      "psutil",
                      "PyAudio",
                      "pocketsphinx",
                      "json_database",
                      "jarbas_utils",
                      "ovos_utils",
                      "speech2text==0.2.1",
                      "text2speech @ git+https://github.com/Joanguitar/text2speech.git",
                      "playsound",
                      "phoneme_guesser",
                      ],
    #dependency_links=["https://github.com/Uberi/speech_recognition/tarball/master", "https://github.com/Joanguitar/text2speech/tarball/master"],
    include_package_data=True,
    url='https://github.com/OpenJarbas/HiveMind-voice-sat',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Mycroft Voice Satellite',
    entry_points={
        'console_scripts': [
            'HiveMind-voice-sat=mycroft_voice_satellite.__main__:main'
        ]
    }
)
