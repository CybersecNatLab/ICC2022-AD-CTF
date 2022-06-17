from pwn import remote, process
import zlib
import base64
import json
from app.gates import evaluate, VAL_LENGTH
from app.ot import Receiver
from Crypto.Cipher import AES
import sys

PORT = 1236

if len(sys.argv) != 2:
    print('Usage: python3 client.py <server ip>')
    exit(1)


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
        self.r = remote(host, PORT)
        self.r.recvlines(1)
        self.r.sendlineafter(b"token: ", token)

    def set_keyword(self, keyword):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"1")
        self.r.sendlineafter(b"secret: ", keyword)

    def set_public(self, data):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"2")
        self.r.sendlineafter(b"text: ", data)

    def get_public(self, user):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"4")
        self.r.sendlineafter(b"user: ", user)
        return self.r.recvline(False).decode()

    def run_function(self, choice, user, my_in):
        self.r.recvlines(6)
        self.r.sendlineafter(b"> ", b"3")
        self.r.sendlineafter(b"user: ", user)
        self.r.recvlines(3)
        self.r.sendlineafter(b"> ", str(choice).encode())

        SIZE = 0
        data = self.r.recvline(False)
        SIZE += len(data)
        tmp = zlib.decompress(base64.b64decode(data))
        obj = json.loads(tmp.decode())
        print("Received object")
        circ = obj["circuit"]

        N, e, x = obj["ot"]["N"], obj["ot"]["e"], obj["ot"]["x"]
        in_B = bytes2bits(my_in)
        assert len(in_B) == 128

        if choice == 2:
            in_B = in_B[::-1]
        receiver = Receiver(in_B)
        v = receiver.round2((N, e), x)
        vdict = json.dumps({"v": v})
        SIZE += len(vdict)
        self.r.sendline(vdict)
        data = self.r.recvline(False)
        SIZE += len(data)
        obj = json.loads(data.decode())
        c = obj["c"]
        m = receiver.decode(c)

        enc_B = [f'{x:010x}' for x in m]
        print("Done OT")

        res = evaluate(circ["gates"], (circ["enc_A"], enc_B), circ["wires_out"])
        if choice == 2:
            res = res[::-1]
        print("Total bytes transferred", SIZE)
        return bits2bytes(res)


token = "..."
user = b"drago"
key = b"A"*16
data = b"Z"*32

choice = 0

if choice == 0:
    # Put and retrieve data
    c = Client(sys.argv[1], token)
    c.set_keyword(key)
    c.set_public(data)
    val = c.get_public(user)

    cipher = AES.new(key.encode(), AES.MODE_ECB)
    print(cipher.decrypt(bytes.fromhex(val)))

if choice == 1:
    # Run echo on self
    c = Client(sys.argv[1], token)
    pt = b"rn4l2p54"*2
    out = c.run_function(1, user, pt)
    print(out)

if choice == 2:
    # Run encrypt on self
    c = Client(sys.argv[1], token)
    pt = b"rn4l2p54"*2
    out = c.run_function(2, user, pt)
    print(out)
