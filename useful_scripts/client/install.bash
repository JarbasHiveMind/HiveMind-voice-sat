python3 -m pip install --upgrade pip
python3 install virtualenv
python3 -m virtualenv .venv

source $(pwd)/.venv/bin/activate

python3 -m pip install git+https://github.com/Joanguitar/HiveMind-voice-sat
