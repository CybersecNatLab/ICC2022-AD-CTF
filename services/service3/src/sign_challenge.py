#!/usr/bin/env python3
import ed25519_blake2b
import sys
import pwn

with open(sys.argv[1], "rb") as f:
    sk = ed25519_blake2b.SigningKey(f.read())

while True:
    s = input("Challenge: ")
    b = pwn.unhex(s.replace("\n", "").replace(" ", ""))
    print(pwn.enhex(sk.sign(b)))
