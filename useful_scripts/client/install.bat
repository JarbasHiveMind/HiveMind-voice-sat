pip install --upgrade pip
pip install virtualenv
python -m virtualenv venv

:: Install pipwin
.\venv\Scripts\pip install pipwin
.\venv\Scripts\pipwin install pyaudio
.\venv\Scripts\pipwin install pocketsphinx

:: Install
.\venv\Scripts\pip install git+https://github.com/Joanguitar/HiveMind-voice-sat

:: Replace playaudio with the repo one (temporary until the update the windows fix)
.\venv\Scripts\pip uninstall -y playsound
.\venv\Scripts\pip install git+https://github.com/TaylorSMarks/playsound

:: Replace text2speech with a windows compatible one
.\venv\Scripts\pip install git+https://github.com/Joanguitar/text2speech
