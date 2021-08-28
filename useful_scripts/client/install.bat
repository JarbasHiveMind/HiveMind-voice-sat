pip install --upgrade pip
pip install virtualenv
python -m virtualenv .venv

:: Install pipwin
.\.venv\Scripts\pip install pipwin
.\.venv\Scripts\pipwin install pyaudio
.\.venv\Scripts\pipwin install pocketsphinx

:: Install
.\.venv\Scripts\pip install -r .\extra-requirements.txt
.\.venv\Scripts\pip install git+https://github.com/Joanguitar/HiveMind-voice-sat

:: Install playsound
.\.venv\Scripts\pip install playsound
