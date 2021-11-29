from setuptools import setup

setup(
    name='HiveMind-voice-sat',
    version='2.0.0a1',
    packages=['hivemind_voice_satellite'],
    install_requires=["hivemind_bus_client",
                      "ovos_utils>=0.0.12a9",
                      "ovos-plugin-manager~=0.0.3a3post1",
                      "ovos-core~=0.0.2a1",
                      "SpeechRecognition~=3.8.1",
                      "PyAudio"],
    include_package_data=True,
    url='https://github.com/OpenJarbas/HiveMind-voice-sat',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Hivemind Voice Satellite',
    entry_points={
        'console_scripts': [
            'HiveMind-voice-sat=hivemind_voice_satellite.__main__:main'
        ]
    }
)
