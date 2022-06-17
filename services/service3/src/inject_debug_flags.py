#!/usr/bin/env python3
import string
import hashlib
import ed25519_blake2b
import pwn
import random

DEBUG_SIGNING = False

sk_checker = b"\xb5\x18\x9fg\r\xd2k\x83v\xd3\xf5\xc4\x02\x17\xbfT\xc9\xd8o\xc9\xc1\xde$\xbc\xc9\xd5\xb3\xd6.\x9d(\x9c"
sk1 = b"\xc5\x07q\xabZ\xcea\x80\xffm\xc5-\xd1r\x05\xd8\xac\x15\xc7j\x1ar\x9b\xdcr\x95\x98\x96A\x9e\x1ei"
sk2 = b"\xe4Z\r\x85\x10/Lb\xf5<}\x03\xb2E\xf5/\x84\xb2\xa1Rd\x1e\xcb\xe1\xdfHwE\xb8\x82\\\n"
sk3 = b"\xa6\xe2\xd9R\x93\x04t\x15\xe0\x83\xd8\xdcw\xdf\xd7#\xac\xec\xb2\xd8yJ\x00\xe9\x9c\x96\xf2O]U-\x0f"
sk4 = b"\xd1\x84\x05(\x99W\x9e\xc1\xdcX\x05YuI\x89F\r\x17\xdd\x07\xcc\xcfH\xe5\xa4\x9f!#c\xd8\xd2\xf2"
sk5 = b"/G\x92\xc8|\xa3\x06{\xbe\xab\x1d\x82\xd9~\xa2\xf5\xf4_\xcabi\xfc\xbag\x14\xd9\x85\xc9\xb4\xf4\xb2\x1c"
sk6 = b"\x8bP\x1c\xec\xa0\x16\x00\xe3\xdc'\x14hliW\xd8\x8b\xf7\xe3\x07$y%\xd5\xfa\xa7\xb4\xe37\xdcV\x93"
sk7 = b'\xed|^\xd4\x95$\x8d\xdb\x97\xfa~"\xdc\x9bLU\r1\xbc5>\xe5}L\xcf\xfd\x88\xd2\x11\x94\xad\x19'
signing_keys = [sk_checker, sk1, sk2, sk3, sk4, sk5, sk6, sk7]  # , sk8, sk9]
assert len(signing_keys) == 8  # checker + 7 teams


def build_flag_name(flag, store):
    assert store == 1 or store == 2
    # print(f'build_flag_name({flag=}, {store=})')
    hash = hashlib.sha256(flag.encode())
    hx = hash.hexdigest()
    return "f" + hx[:30] + str(store)


io = pwn.remote("127.0.0.1", 1337)
io.recvuntil(b"Ready")
# N_FLAGS = 64
N_FLAGS = 128
for i, letter in zip(range(N_FLAGS), string.ascii_letters * (N_FLAGS // 52 + 1)):
    # nk = random.randint(0, len(signing_keys)-1)
    nk = i % 8
    if DEBUG_SIGNING:
        print(f"{nk=} ", end="")
    sk = ed25519_blake2b.SigningKey(signing_keys[nk])
    if N_FLAGS < 100:
        flag_value = f"FLAG{i:02}" * 5 + "Z="
    else:
        flag_value = f"FLAG{i:03}" * 4 + "ABC="
    assert len(flag_value) == 32
    io.sendline(f'"{flag_value}"'.encode())
    io.recvuntil(b"Ready")
    id = build_flag_name(flag_value, i // (N_FLAGS // 2) + 1)
    io.sendline(id.encode())
    io.recvuntil(b"Ready")
    io.sendline(b"Set_var")
    io.recvuntil(b"you must tell me the signature for:\n")
    b = pwn.unhex(io.recvline().decode().replace("\n", "").replace(" ", ""))
    assert len(b) == 16
    io.sendline(pwn.enhex(sk.sign(b)).encode())
    if DEBUG_SIGNING:
        io.recvuntil(b"Signed with key=")
        signed_with = int(io.recvline().decode())
        print(signed_with)
        assert nk == signed_with
    io.recvuntil(b"Ready")
