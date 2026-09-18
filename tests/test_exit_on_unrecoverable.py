"""An unrecoverable listener failure ends the process.

``OVOSDinkumVoiceService.run`` is a thread body: when the voice loop raises it
logs, sets the error status and calls ``stop()``, leaving the process alive with
nothing reading the microphone. A service manager sees a healthy unit and
restarts nothing, so the satellite stays deaf. Ending the process is what makes
a restart policy work.
"""
import subprocess
import sys
from unittest.mock import patch

from hivemind_voice_satellite.service import UNRECOVERABLE, on_error


def test_on_error_ends_the_process():
    with patch("hivemind_voice_satellite.service.os._exit") as exit_:
        on_error("voice_loop failed")
    exit_.assert_called_once_with(UNRECOVERABLE)


def test_on_error_ends_the_process_from_a_background_thread():
    """sys.exit in a thread unwinds the thread only; the exit must not.

    Run it for real in a subprocess rather than asserting on a mock, so the
    claim is about the process and not about the call.
    """
    program = (
        "import threading\n"
        "from hivemind_voice_satellite.service import on_error\n"
        "t = threading.Thread(target=on_error, args=('voice_loop failed',))\n"
        "t.start()\n"
        "t.join(5)\n"
        "print('STILL ALIVE')\n"
    )
    done = subprocess.run([sys.executable, "-c", program],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == UNRECOVERABLE, (
        f"process survived a listener failure raised on a background thread: "
        f"rc={done.returncode} stdout={done.stdout!r}"
    )
    assert "STILL ALIVE" not in done.stdout
