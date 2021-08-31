from setuptools import setup

setup(
    name='HiveMind-voice-sat',
    version='1.0.8',
    packages=['mycroft_voice_satellite',
              'mycroft_voice_satellite.speech',
              'mycroft_voice_satellite.res',
              'mycroft_voice_satellite.configuration'],
    install_requires=["psutil",
                      "jarbas_hive_mind>=0.10.3",
                      "pyee",
                      "requests",
                      "PyAudio==0.2.11",
                      "ovos_utils>=0.0.12a9",
                      "requests_futures",
                      "json_database>=0.1.3",
                      "phoneme_guesser>=0.1.0",
                      "ovos-plugin-manager>=0.0.1",
                      "ovos-ww-plugin-pocketsphinx>=0.1.0",
                      "ovos-tts-plugin-responsivevoice>=0.1",
                      "ovos-stt-plugin-chromium>=0.1.1"],
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
