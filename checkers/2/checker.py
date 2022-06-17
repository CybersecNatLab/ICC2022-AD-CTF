#!/usr/bin/env python3

# Do not make modification to checklib.py (except for debug), it can be replaced at any time
import checklib
import random
import string
import sys
import os
os.environ["PWNLIB_NOTERM"] = "1"

from pwn import *
from service2_client import Client

context.timeout = 5
context.log_level = "error"

data = checklib.get_data()
action = data['action']
auth_port = 1234
store1_port = 1235
service_name = 'ExamNotes'

team_id = data['teamId']
team_addr = '10.60.' + team_id + '.1'


def get_random_string(n):
    alph = string.ascii_letters + string.digits
    return "".join(random.choice(alph) for _ in range(n))

# Check SLA


def check_sla():
    number_of_notes = random.randint(1, 5)
    username = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))
    note_titles = [get_random_string(random.randint(10, 16))
                   for _ in range(number_of_notes)]
    note_contents = [get_random_string(random.randint(
        20, 100)) for _ in range(number_of_notes)]

    c = Client(team_addr, auth_port, username, password,
               "1")  # last param is flagstore id
    try:
        c.register()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot register", str(e))

    try:
        c.login()
        login_token = c.get_token()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot get login token from auth", str(e))

    try:
        r = remote(team_addr, store1_port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot connect to ExamNotes", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(login_token.encode())
        r.recvline()
        assert r.recvline().startswith(b"Successfully authenticated")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot login via token on ExamNotes", str(e))

    try:
        for i in range(number_of_notes):
            r.recvuntil(b'0. Exit\n')
            r.sendline(b"1")
            r.recvuntil(b": ")
            r.sendline(note_titles[i].encode())
            r.recvuntil(b": ")
            r.sendline(note_contents[i].encode())
            assert b"added" in r.recvline()
        r.close()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot create a new note on ExamNotes", str(e))

    try:
        r = remote(team_addr, store1_port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot connect to ExamNotes", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(login_token.encode())
        r.recvline()
        assert r.recvline().startswith(b"Successfully authenticated")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot login via token on ExamNotes", str(e))

    try:
        for _ in range(random.randint(1, 3)):
            if random.randint(0, 1) == 0:
                r.recvuntil(b'0. Exit\n')
                r.sendline(b"2")
                recovered_notes = r.recvlines(number_of_notes)
                assert all([note_titles[i].encode() in b"".join(
                    recovered_notes) for i in range(number_of_notes)])
            else:
                r.recvuntil(b'0. Exit\n')
                r.sendline(b"3")
                r.recvuntil(b": ")
                note_id = random.randint(0, number_of_notes-1)
                r.sendline(str(note_id).encode())
                assert note_titles[note_id].encode() in r.recvline()
                assert note_contents[note_id].encode() in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot list or read notes on ExamNotes", str(e))

    checklib.quit(checklib.Status.OK, 'OK')


# Put the flag using the flag as the seed for random stuff
def put_flag():
    flag = data['flag']

    random.seed(int.from_bytes(flag.encode(), "big"))
    username = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))

    c = Client(team_addr, auth_port, username, password,
               "1")  # last param is flagstore id
    try:
        c.register()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot register", str(e))

    try:
        c.login()
        login_token = c.get_token()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot get login token from auth", str(e))

    try:
        r = remote(team_addr, store1_port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot connect to ExamNotes", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(login_token.encode())
        r.recvline()
        assert r.recvline().startswith(b"Successfully authenticated")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot login via token on ExamNotes", str(e))

    try:
        r.recvuntil(b'0. Exit\n')
        r.sendline(b"1")
        r.recvuntil(b": ")
        r.sendline(b"flag")
        r.recvuntil(b": ")
        r.sendline(flag.encode())
        assert b"added" in r.recvline()
        r.close()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot create a new note on ExamNotes", str(e))

    checklib.post_flag_id(service_name, team_addr, username)

    # If OK
    checklib.quit(checklib.Status.OK, 'OK')

# Check if the flag still exists, use the flag as the seed for random stuff as for put flag


def get_flag():

    flag = data['flag']

    random.seed(int.from_bytes(flag.encode(), "big"))
    username = get_random_string(random.randint(10, 16))
    password = get_random_string(random.randint(10, 16))

    c = Client(team_addr, auth_port, username, password,
               "1")  # last param is flagstore id
    try:
        c.login()
        login_token = c.get_token()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot get login token from auth", str(e))

    try:
        r = remote(team_addr, store1_port)
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot connect to ExamNotes", str(e))

    try:
        r.recvuntil(b": ")
        r.sendline(login_token.encode())
        r.recvline()
        assert r.recvline().startswith(b"Successfully authenticated")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot login via token on ExamNotes", str(e))

    try:
        r.recvuntil(b'0. Exit\n')
        r.sendline(b"3")
        r.recvuntil(b": ")
        note_id = 0
        r.sendline(str(note_id).encode())
        assert b"flag" in r.recvline()
        assert flag.encode() in r.recvline()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot retrieve flag", str(e))

    checklib.quit(checklib.Status.OK, 'OK')


if __name__ == "__main__":

    if action == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif action == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif action == checklib.Action.GET_FLAG.name:
        get_flag()
