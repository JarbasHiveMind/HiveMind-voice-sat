from setuptools import setup

setup(
    name='HiveMind-voice-sat',
    version='1.0.0',
    packages=['mycroft_voice_satellite'],
    install_requires=["jarbas_hive_mind>=0.8.0",
                      "SpeechRecognition==3.8.1",
                      "pyee",
                      "requests",
                      "PyAudio==0.2.11",
                      "pocketsphinx==0.1.15",
                      "jarbas_utils",
                      "gtts"],
    include_package_data=True,
    url='https://github.com/OpenJarbas/HiveMind-voice-sat',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Mycroft Voice Satellite'
)
