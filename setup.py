from setuptools import setup

setup(
    name='HiveMind-voice-sat',
    version='1.0.7',
    packages=['mycroft_voice_satellite', 'mycroft_voice_satellite.speech',
              'mycroft_voice_satellite.res',
              'mycroft_voice_satellite.configuration'],
    install_requires=["jarbas_hive_mind>=0.10.3",
                      "speech2text",
                      "pyee",
                      "requests",
                      "requests_futures",
                      "psutil",
                      "PyAudio==0.2.11",
                      "pocketsphinx==0.1.15",
                      "ovos_utils",
                      "text2speech>=0.1.9"],
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
