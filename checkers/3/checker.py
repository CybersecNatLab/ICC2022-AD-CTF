#!/usr/bin/env python3

# Do not make modification to checklib.py (except for debug), it can be replaced at any time
import checklib
import random
import string
from hashlib import sha256
import zlib
import base64
import json
from Crypto.Cipher import AES
import os
os.environ["PWNLIB_NOTERM"] = "1"

from pwn import *
from service2_client import Client as AuthClient

context.timeout = 5
context.log_level = "error"

data = checklib.get_data()
action = data['action']
rd = data['round']
team_id = data['teamId']
team_addr = '10.60.' + team_id + '.1'
port = 1236
auth_port = 1234
service_name = "EncryptedNotes"


def random_string(min, max):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(random.randint(min, max)))


# Auth stuff
def get_random_creds():
    username = random_string(8, 24)
    password = random_string(8, 24)
    return username, password


def register_random_user():
    try:
        username, password = get_random_creds()
        c = AuthClient(team_addr, auth_port, username, password, "2")
        c.register()
        return username, password
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t register user on auth service', str(e))


def get_token(username, password):
    try:
        c = AuthClient(team_addr, auth_port, username, password, "2")
        c.login()
        token = c.get_token()
        return token
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t get a token from auth service', str(e))


# OT stuff
class Receiver:
    def __init__(self, b):
        self.b = b

    def round2(self, pk, x):
        N, e = pk
        n = len(x)
        assert n == len(self.b)

        v = []
        k = []
        for i in range(n):
            kk = random.randrange(1 << 2048)
            k.append(kk)
            cur = x[i][self.b[i]] + pow(kk, e, N)
            v.append(cur % N)
        self.k = k
        self.N = N
        return v

    def decode(self, c):
        n = len(c)
        assert n == len(self.b)

        m = []
        for i in range(n):
            mm = (c[i][self.b[i]]-self.k[i]) % self.N
            m.append(mm)
        return m


# GC evaluation
VAL_LENGTH = 5
PAD_LENGTH = 3


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def H(k):
    return sha256(k).digest()


def dec(k, x):
    k = H(k)
    val = xor(k, x)
    if val[:PAD_LENGTH] == b"\0"*PAD_LENGTH:
        return val[PAD_LENGTH:]


def decode_gate(opv, g, ins, to_hex):
    if to_hex:
        ins = [bytes.fromhex(x) for x in ins]
        g = [bytes.fromhex(r) for r in g]
    if opv == "INV":
        res = ins[0]
    elif opv == "XOR":
        res = xor(ins[0], ins[1])
    else:
        for x in g:
            k = b"".join(ins)
            val = dec(k, x)
            if val is not None:
                res = val
                break
    if to_hex:
        return res.hex()
    return res


def evaluate(garbled_circuit, inputs, wires_out, to_hex=True):
    enc_A, enc_B = inputs
    vals = enc_A+enc_B+[None]*len(garbled_circuit)
    for g in garbled_circuit:
        idx, opv, ins, gate = g
        k = [vals[i] for i in ins]
        cur = decode_gate(opv, gate, k, to_hex)
        assert cur is not None
        vals[idx] = cur

    n_outs = len(wires_out)
    vals_out = vals[-n_outs:]
    out = [w.index(v) for v, w in zip(vals_out, wires_out)]
    return out


# Client
def bytes2bits(b):
    bits = ''.join(f'{x:08b}' for x in b)
    return list(map(int, bits))


def bits2bytes(arr):
    n = len(arr)
    assert n % 8 == 0
    nbytes = n // 8
    s = "".join(map(str, arr))
    return int.to_bytes(int(s, 2), nbytes, "big")


class Client:
    def __init__(self, host, token):
        self.r = remote(host, port)
        self.r.recvlines(1)
        self.r.sendlineafter(b"token: ", token.encode())

    def set_keyword(self, keyword):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"1")
        self.r.sendlineafter(b"secret: ", keyword.encode())

    def set_public(self, data):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"2")
        self.r.sendlineafter(b"text: ", data.encode())

    def get_public(self, user):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"4")
        self.r.sendlineafter(b"user: ", user.encode())
        return self.r.recvline(False).decode()

    def run_function(self, choice, user, my_in):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"3")
        self.r.sendlineafter(b"user: ", user.encode())
        self.r.recvlines(3)
        self.r.sendlineafter(b"> ", str(choice).encode())

        data = self.r.recvline(False)
        tmp = zlib.decompress(base64.b64decode(data))
        obj = json.loads(tmp.decode())
        circ = obj["circuit"]

        N, e, x = obj["ot"]["N"], obj["ot"]["e"], obj["ot"]["x"]
        in_B = bytes2bits(my_in)
        assert len(in_B) == 128

        if choice == 2:
            in_B = in_B[::-1]
        receiver = Receiver(in_B)
        v = receiver.round2((N, e), x)
        vdict = json.dumps({"v": v})
        self.r.sendline(vdict.encode())
        data = self.r.recvline(False)
        obj = json.loads(data.decode())
        c = obj["c"]
        m = receiver.decode(c)

        enc_B = [f'{x:010x}' for x in m]

        res = evaluate(circ["gates"], (circ["enc_A"],
                       enc_B), circ["wires_out"])
        if choice == 2:
            res = res[::-1]
        return bits2bytes(res)


# SLA functions
def sla_user_setkeyword():
    try:
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))
    try:
        key = random_string(16, 16)
        rdata = random_string(32, 32)
        c.set_keyword(key)
        c.set_public(rdata)
        return username, key
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t put data', str(e))


def sla_user_echo(target_user, key):
    try:
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))
    try:
        rdata = os.urandom(16)
        res = c.run_function(1, target_user, rdata)
        if res != rdata:
            checklib.quit(checklib.Status.DOWN, 'Echo function not working',
                          f"sla_user_echo input={rdata.hex()} output={res.hex()}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t run echo function', str(e))


def sla_user_encrypt(target_user, key):
    try:
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))
    try:
        rdata = os.urandom(16)
        #print("running GC")
        res = c.run_function(2, target_user, rdata)
        cipher = AES.new(key.encode(), AES.MODE_ECB)
        pt = cipher.decrypt(res)
        if pt != rdata:
            checklib.quit(checklib.Status.DOWN, 'Encrypt function not working',
                          f"sla_user_encrypt input={rdata.hex()} key={key} output={res.hex()}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t run encrypt function', str(e))


def sla_user_readpublic(target_user, key):
    try:
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))
    try:
        res = c.get_public(target_user)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t read public data', str(e))


# Check SLA
def check_sla():

    user, key = sla_user_setkeyword()
    slas = [sla_user_echo, sla_user_encrypt, sla_user_readpublic]

    f = random.choice(slas)
    f(user, key)

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')


# Put the flag using the flag as the seed for random stuff
def put_flag():
    flag = data["flag"]
    try:
        random.seed("123"+flag+"789")
        key = random_string(16, 16)
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))

    try:
        #print("putting flag", username, key)
        c.set_keyword(key)
        c.set_public(flag)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t put data', str(e))

    checklib.post_flag_id(service_name, team_addr, username)

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')


# Get flag functions
def get_flag_pubdata(c, target_user, key):
    try:
        pubdata = c.get_public(target_user)
        ct = bytes.fromhex(pubdata)
        cipher = AES.new(key.encode(), AES.MODE_ECB)
        pt = cipher.decrypt(ct)
        if pt.decode() != data["flag"]:
            checklib.quit(checklib.Status.DOWN, 'Incorrect public data for flag',
                          f"get_flag_pubdata pubdata={pubdata.hex()} key={key} pt={pt.hex()}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t read public data', str(e))


def get_flag_AES(c, target_user, key):
    flag = data["flag"].encode()
    try:
        ct = c.run_function(2, target_user, flag[:16])
        #print("run GC")
        pubdata = c.get_public(target_user)
        if ct.hex() != pubdata[:32]:
            checklib.quit(checklib.Status.DOWN, 'Incorrect encryption function for flag',
                          f"get_flag_AES pubdata={pubdata.hex()} ct={ct.hex()}")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      'Can\'t run encryption function', str(e))


# Check if the flag still exists, use the flag as the seed for random stuff as for put flag
def get_flag():
    flag = data["flag"]
    try:
        username, password = register_random_user()
        token = get_token(username, password)
        c = Client(team_addr, token)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, 'Can\'t login', str(e))

    checks = [get_flag_pubdata, get_flag_AES]
    check = random.choice(checks)

    random.seed("123"+flag+"789")
    key = random_string(16, 16)
    username, password = get_random_creds()
    check(c, username, key)

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
