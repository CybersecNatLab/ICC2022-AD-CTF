#!/usr/bin/env python3
import random

from cmd_paths import cmd_paths as cmds


def encode(path: str):
    s = ["a"] * 21
    indexes = sorted(random.sample(range(len(s)), len(path)))
    for i, direction in zip(indexes, path):
        s[i] = direction
    b = ""
    for c in s:
        if c == "l":
            b = "010" + b
        elif c == "r":
            b = "101" + b
        else:
            b = random.choice(["001", "011", "100", "110"]) + b
    return int(b, 2)


def print_encodings(name, path):
    print(f"{name} {path} -> ", end="")
    for _ in range(3):
        print(encode(path), end=" ")
    print()


for name, path in cmds.items():
    print_encodings(name, path)
