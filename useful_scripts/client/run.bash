host="wss://192.168.0.116"
name="TestUser"
access_key="WeakestPasswordEver"
crypto_key=""
port="5678"

source $(pwd)/.venv/bin/activate
if [ ${crypto_key}=="" ]
then
  python3 -m mycroft_voice_satellite --host ${host} --name ${name} --access_key ${access_key} --port ${port}
else
  python3 -m mycroft_voice_satellite --host ${host} --name ${name} --access_key ${access_key} --crypto_key ${crypto_key} --port ${port}
fi
