import os
from setuptools import setup

BASEDIR = os.path.abspath(os.path.dirname(__file__))



def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
            print('USING LOOSE REQUIREMENTS!')
            requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]



setup(
    name='HiveMind-voice-sat',
    version='2.0.0a1',
    packages=['hivemind_voice_satellite'],
    install_requires=required("requirements.txt"),
    include_package_data=True,
    url='https://github.com/OpenJarbas/HiveMind-voice-sat',
    license='MIT',
    author='jarbasAI',
    author_email='jarbasai@mailfence.com',
    description='Hivemind Voice Satellite',
    entry_points={
        'console_scripts': [
            'hivemind-voice-sat=hivemind_voice_satellite.__main__:connect'
        ]
    }
)
