set host=wss://192.168.0.161
set name=TestUser
set access_key=WeakestPasswordEver
set crypto_key=
set port=5678

IF "%crypto_key%"=="" (.\.venv\Scripts\activate.bat & python -m mycroft_voice_satellite --host %host% --name %name% --access_key %access_key% --port %port%) ELSE (.\.venv\Scripts\activate.bat & python -m mycroft_voice_satellite --host %host% --name %name% --access_key %access_key% --crypto_key %crypto_key% --port %port%)
