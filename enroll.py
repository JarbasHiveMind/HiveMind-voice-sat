from jarbas_hive_mind.database import ClientDatabase

name = "JarbasCliTerminal"
access_key = "RESISTENCEisFUTILE"
crypto_key = "resistanceISfutile"
mail = "remote_cli@hivemind.com"


with ClientDatabase() as db:
    db.add_client(name, mail, access_key, crypto_key=crypto_key)
