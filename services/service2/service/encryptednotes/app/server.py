from gates import build_circuit_echo, build_circuit_AES128, garble
from ot import Sender
import json
import zlib
import base64
from hashlib import sha256
import os
import string
from Crypto.Cipher import AES
from auth import handle_token

alphabet = string.digits+string.ascii_letters+string.punctuation


def decode_token(token):
    #return token
    return handle_token(token)


def do_mkdir(fn):
    if not os.path.isdir(fn):
        os.mkdir(fn)


def write_file(user, name, get_val):
    fn = sha256(user.encode()).hexdigest()
    base_dir = f"data/{fn}"
    do_mkdir(base_dir)
    path = os.path.join(base_dir, name)
    if os.path.exists(path):
        print(f"You already set a {name}!")
        exit(0)
    val = get_val()
    try:
        open(path, "x").write(val)
    except:
        print("Something went wrong!")
        exit(1)


def read_file(user, name):
    fn = sha256(user.encode()).hexdigest()
    base_dir = f"data/{fn}"
    if not os.path.isdir(base_dir):
        print("The user didn't save anything!")
        exit(1)
    path = os.path.join(base_dir, name)
    if not os.path.isfile(path):
        print(f"The {name} file doesn't exist!")
        exit(1)
    try:
        val = open(path).read().strip()
        return val
    except:
        print("Something went wrong!")
        exit(1)


def set_keyword(user):
    def get_val():
        keyword = input("Tell me a secret: ")
        if len(keyword) != 16 or not all(s in alphabet for s in keyword):
            print("This is a strange keyword...")
            exit(0)
        return keyword

    write_file(user, "keyword", get_val)


def get_keyword(user):
    keyword = read_file(user, "keyword")
    assert len(keyword) == 16
    return keyword


def set_public(user):
    def get_val():
        keyword = get_keyword(user)
        plaintext = input("Tell me a piece of text: ")
        if len(plaintext) != 32 or not all(s in alphabet for s in keyword):
            print("This is a strange text...")
            exit(0)
        cipher = AES.new(keyword.encode(), AES.MODE_ECB)
        ct = cipher.encrypt(plaintext.encode())
        return ct.hex()

    write_file(user, "data", get_val)


def get_public():
    user = input("Choose a user: ")
    ct = read_file(user, "data")
    assert len(ct) == 64
    print(ct)


def bytes2bits(b):
    bits = ''.join(f'{x:08b}' for x in b)
    return list(map(int, bits))


circuits = {
    1: build_circuit_echo,
    2: build_circuit_AES128
}


def private_encrypt():
    user = input("Choose a user: ")
    keyword = get_keyword(user)

    print("Choose a circuit")
    print("1. Echo")
    print("2. Encrypt")
    c = int(input("> "))
    circuit = circuits[c]()

    true_input = bytes2bits(keyword.encode())
    if c == 2:
        true_input = true_input[::-1]

    (enc_A, enc_B), garbled_circuit, wires_out = garble(circuit, true_input)
    enc_B_num = [[int(x[0], 16), int(x[1], 16)] for x in enc_B]
    sender = Sender(enc_B_num)
    (N, e), x = sender.round1()

    data = {
        "circuit": {
            "enc_A": enc_A,
            "gates": garbled_circuit,
            "wires_out": wires_out
        },
        "ot": {
            "N": N,
            "e": e,
            "x": x
        }
    }
    compressed = zlib.compress(json.dumps(data).encode())
    to_send = base64.b64encode(compressed)
    print(to_send.decode())

    recv = json.loads(input())
    v = recv["v"]

    c = sender.round3(v)
    print(json.dumps({"c": c}))


def main():
    print("Welcome to EncryptedNotes!")
    token = input("Input your token: ")
    user = decode_token(token)

    while True:
        print("What do you want to do?")
        print("1. Set a keyword")
        print("2. Public encrypt")
        print("3. Private encrypt")
        print("4. Read public")
        print("5. Quit")
        choice = int(input("> "))
        if choice == 1:
            set_keyword(user)
        if choice == 2:
            set_public(user)
        if choice == 3:
            private_encrypt()
        if choice == 4:
            get_public()
        if choice == 5:
            exit(0)


if __name__ == "__main__":
    main()
