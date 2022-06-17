import json
from Crypto.Cipher import AES
import sys
import time
import string
import os

APP_KEY = os.environ["EncryptedNotesKey"].encode()

ALPH = string.ascii_letters + string.digits

def validate_string(s):
    return all([c in ALPH for c in s]) and len(s) > 7 and len(s) < 65

def handle_token(token):
    try:
        app_token, service_token = [bytes.fromhex(x) for x in token.split(".")]
        cipher = AES.new(APP_KEY, AES.MODE_CTR, nonce = service_token[:8], initial_value = service_token[8:16])
        service_token = json.loads(cipher.decrypt(service_token[16:]))
        user1 = bytes.fromhex(service_token["user"])
        key = bytes.fromhex(service_token["key"])
        cipher = AES.new(key, AES.MODE_CTR, nonce = app_token[:8], initial_value = app_token[8:16])
        app_token = json.loads(cipher.decrypt(app_token[16:]))
        user2 = bytes.fromhex(app_token["user"])
        cur_time = int(time.time())
        assert service_token["type"] == "SERVICE_TOKEN"
        assert app_token["type"] == "APP_TOKEN"
        assert abs(cur_time-int(app_token["ts"]))<120 and abs(cur_time-int(service_token["ts"]))<120
        assert user1 == user2
        assert validate_string(user1.decode())
        return user1.decode()
    except:
        return None
