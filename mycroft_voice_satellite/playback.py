from ovos_utils.sound import play_audio as _play_audio, \
    play_wav as _play_wav, play_mp3 as _play_mp3, play_ogg as _play_ogg
from mycroft_voice_satellite.configuration import CONFIGURATION
from os.path import join, dirname, expanduser, normpath, abspath, isfile


def play_audio(uri):
    cmd = CONFIGURATION["playback"]["play_fallback_cmd"]
    return _play_audio(uri, cmd)


def play_wav(uri):
    cmd = CONFIGURATION["playback"]["play_wav_cmd"]
    return _play_wav(uri, cmd)


def play_mp3(uri):
    cmd = CONFIGURATION["playback"]["play_mp3_cmd"]
    return _play_mp3(uri, cmd)


def play_ogg(uri):
    cmd = CONFIGURATION["playback"]["play_ogg_cmd"]
    return _play_ogg(uri, cmd)


def resolve_resource_file(res_name):
    """Convert a resource into an absolute filename.

    Resource names are in the form: 'filename.ext'
    or 'path/filename.ext'

    The system wil look for ~/.mycroft/res_name first, and
    if not found will look at /opt/mycroft/res_name,
    then finally it will look for res_name in the 'mycroft/res'
    folder of the source code package.

    Example:
    With mycroft running as the user 'bob', if you called
        resolve_resource_file('snd/beep.wav')
    it would return either '/home/bob/.mycroft/snd/beep.wav' or
    '/opt/mycroft/snd/beep.wav' or '.../mycroft/res/snd/beep.wav',
    where the '...' is replaced by the path where the package has
    been installed.

    Args:
        res_name (str): a resource path/name
    Returns:
        str: path to resource or None if no resource found
    """
    config = CONFIGURATION

    # First look for fully qualified file (e.g. a user setting)
    if isfile(res_name):
        return res_name

    # Now look for ~/.mycroft/res_name (in user folder)
    filename = expanduser("~/.mycroft/" + res_name)
    if isfile(filename):
        return filename

    # Next look for /opt/mycroft/res/res_name
    data_dir = expanduser(config['data_dir'])
    filename = expanduser(join(data_dir, res_name))
    if isfile(filename):
        return filename

    # Finally look for it in the source package
    filename = join(dirname(__file__), 'res', res_name)
    filename = abspath(normpath(filename))
    if isfile(filename):
        return filename

    return None  # Resource cannot be resolved

