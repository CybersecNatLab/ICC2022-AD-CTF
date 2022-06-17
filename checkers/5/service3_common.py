#!/bin/env python3
import checklib
import os
import pwn
import logging
import hashlib
import ed25519_blake2b
import random
import ctypes
import string
import sys
from cmd_paths import cmd_paths
# from pwn import log

SK_CHECKER = ed25519_blake2b.SigningKey(
    b"\xb5\x18\x9fg\r\xd2k\x83v\xd3\xf5\xc4\x02\x17\xbfT\xc9\xd8o\xc9\xc1\xde$\xbc\xc9\xd5\xb3\xd6.\x9d(\x9c")

_team1_skey = ed25519_blake2b.SigningKey(
    b"\xc5\x07q\xabZ\xcea\x80\xffm\xc5-\xd1r\x05\xd8\xac\x15\xc7j\x1ar\x9b\xdcr\x95\x98\x96A\x9e\x1ei")
_team2_skey = ed25519_blake2b.SigningKey(
    b"\xe4Z\r\x85\x10/Lb\xf5<}\x03\xb2E\xf5/\x84\xb2\xa1Rd\x1e\xcb\xe1\xdfHwE\xb8\x82\\\n")
_team3_skey = ed25519_blake2b.SigningKey(
    b"\xa6\xe2\xd9R\x93\x04t\x15\xe0\x83\xd8\xdcw\xdf\xd7#\xac\xec\xb2\xd8yJ\x00\xe9\x9c\x96\xf2O]U-\x0f")
_team4_skey = ed25519_blake2b.SigningKey(
    b"\xd1\x84\x05(\x99W\x9e\xc1\xdcX\x05YuI\x89F\r\x17\xdd\x07\xcc\xcfH\xe5\xa4\x9f!#c\xd8\xd2\xf2")
_team5_skey = ed25519_blake2b.SigningKey(
    b"/G\x92\xc8|\xa3\x06{\xbe\xab\x1d\x82\xd9~\xa2\xf5\xf4_\xcabi\xfc\xbag\x14\xd9\x85\xc9\xb4\xf4\xb2\x1c")
_team6_skey = ed25519_blake2b.SigningKey(
    b"\x8bP\x1c\xec\xa0\x16\x00\xe3\xdc'\x14hliW\xd8\x8b\xf7\xe3\x07$y%\xd5\xfa\xa7\xb4\xe37\xdcV\x93")
_team7_skey = ed25519_blake2b.SigningKey(
    b'\xed|^\xd4\x95$\x8d\xdb\x97\xfa~"\xdc\x9bLU\r1\xbc5>\xe5}L\xcf\xfd\x88\xd2\x11\x94\xad\x19')
_teams_signing_keys = [_team1_skey, _team2_skey, _team3_skey,
                       _team4_skey, _team5_skey, _team6_skey, _team7_skey]

MIN_LONG = -2**63
MAX_LONG = 2**63-1

FLAG_STORE = int(os.environ["FLAG_STORE"])
assert FLAG_STORE == 1 or FLAG_STORE == 2

pwn.context.timeout = 10
pwn.context.log_level = logging.ERROR
# pwn.context.log_level = logging.DEBUG

if __name__ != '__main__':
    data = checklib.get_data()
    ACTION = data["action"]
    ROUND = data["round"]
else:
    assert "LOCALHOST_RULEZ" in os.environ
    ROUND = str(random.randint(0, 200))


def get_team_ip():
    if "LOCALHOST_RULEZ" in os.environ:
        return "127.0.0.1"
    return "10.60." + data["teamId"] + ".1"


def get_team_port():
    if "LOCALHOST_RULEZ" in os.environ:
        return 1337
    return 1337  # FIXME


def connect_to_service():
    try:
        return pwn.remote(get_team_ip(), get_team_port())
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot connect", str(e))


def grab_banner(io):
    try:
        io.recvuntil(
            b"_______ ______    ____     ____  _____   |  |    ____   __ __ |  |  _____   _/  |_   ____  _______ \n")
        io.recvuntil(b"The value stack is empty")
        io.recvuntil(b"Ready")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN,
                      "Cannot grab banner/prompt", str(e))


def test_get_var(io):
    try:
        r = int(ROUND)
    except:
        # log.warning("Cannot convert ROUND to integer")
        return True
    try:
        var_name = _gen_var_name(f'{r-1}')
        # log.info(f'Testing get_var({var_name})')
        commands = ""
        commands += f"{var_name}{s()}"
        commands += f"Get_var{s()}"
        if rand_bool():
            commands += f"Clear\n"
        else:
            commands += f"Drop\n"
        io.send(commands.encode())
    except SystemExit:
        raise
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot get a variable",
                      f"Exception: {type(e)} {str(e)}")
    return True


def _gen_var_name(r):
    hash = hashlib.sha256(r.encode() + b"birubiru")
    not_so_random = random.Random(hash.digest())
    if not_so_random.randint(0, 2) == 0:
        var_name = (
            not_so_random.choice(string.ascii_lowercase + "_")
            + "".join(not_so_random.sample(string.ascii_letters +
                      string.digits + "_", random.randint(0, 31)))
        )
    else:
        var_name = not_so_random.choice(string.ascii_lowercase)
    return var_name


def _gen_var_value(r):
    hash = hashlib.sha256(r.encode() + b"pippero")
    not_so_random = random.Random(hash.digest())
    if not_so_random.randint(0, 2) == 0:
        var_value = "".join(not_so_random.sample(
            string.ascii_letters + string.digits + "_", not_so_random.randint(0, 32)))
    elif not_so_random.randint(0, 1) == 0:
        var_value = not_so_random.randint(MIN_LONG, MAX_LONG)
    else:
        var_value = not_so_random.randint(0, 255)
    return var_value


def test_set_var(io):
    try:
        var_name = _gen_var_name(ROUND)
        var_value = _gen_var_value(ROUND)
        # log.info(f'Testing set_var({var_name}, {var_value})')
        commands = f"{repr(var_value)}{s()}"
        commands += f"{var_name}{s()}"
        commands += f"Set_var\n"
        # with open("/tmp/test_commands", "a") as f:
        #     f.write(commands)
        io.send(commands.encode())
        output = io.recvuntil(b"you must tell me the signature for:\n")
        if b'you must tell' not in output:
            # print("\n\n---")
            # print(output.decode())
            # print("--\n\n")
            checklib.quit(checklib.Status.DOWN, "Cannot set a variable",
                          "Service doesn't ask for signature when using a random (team) key")
        b = pwn.unhex(io.recvline().decode().replace(
            "\n", "").replace(" ", ""))
        assert len(b) == 16
        io.sendline(pwn.enhex(random.choice(
            _teams_signing_keys).sign(b)).encode())
        output = io.recvuntil(b"The value stack is empty")
        if b'The value stack is empty' not in output:
            # print("\n\n---")
            # print(output.decode())
            # print("--\n\n")
            checklib.quit(checklib.Status.DOWN, "Cannot set a variable",
                          "Service doesn't reply when using a random signature")
    except SystemExit:
        raise
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot set a variable",
                      f"Exception: {type(e)} {str(e)}")
    return True


def check_sla():
    # log.info('Checking SLA')
    io = connect_to_service()
    grab_banner(io)
    try:
        for _ in range(5):
            if random.randint(0, 3) == 0 and not test_push_int(io):
                checklib.quit(checklib.Status.DOWN,
                              "Bad evaluation", "test_push_int failed")
            if random.randint(0, 3) == 0 and not test_push_str(io):
                checklib.quit(checklib.Status.DOWN,
                              "Bad evaluation", "test_push_str failed")
            if random.randint(0, 3) == 0 and not test_push_id(io):
                checklib.quit(checklib.Status.DOWN,
                              "Bad evaluation", "test_push_id failed")
            if random.randint(0, 3) == 0 and not test_set_var(io):
                checklib.quit(checklib.Status.DOWN,
                              "Bad evaluation", "test_set_var failed")
            if random.randint(0, 3) == 0 and not test_get_var(io):
                checklib.quit(checklib.Status.DOWN,
                              "Bad evaluation", "test_get_var failed")
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Connection prematurely closed", str(e))
    try:
        io.close()
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot close the connection properly", str(e))
    checklib.quit(checklib.Status.OK, "OK")


def put_flag():
    io = connect_to_service()
    grab_banner(io)
    flag_value = data["flag"]
    flag_name = build_flag_name(flag_value)
    # log.info(f'put_flag({flag_name}, {flag_value})')
    try:
        commands = ""
        if rand_bool():
            commands += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}"
        if rand_bool():
            commands += f"{push_str(flag_value)}"
            if rand_bool():
                commands += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}"
            commands += f"{push_id(flag_name)}"
        else:
            commands += f"{push_id(flag_name)}"
            if rand_bool():
                commands += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}"
            commands += f"{push_str(flag_value)}{rand_encode('swap')}{s()}"
        commands += f"{rand_encode('set_var')}\n"
        # with open("/tmp/test_commands", "w") as f:
        #     f.write(commands)
        io.send(commands.encode())
        output = io.recvuntil(b"you must tell me the signature for:\n")
        if b'you must tell' not in output:
            # print("\n\n---")
            # print(output.decode())
            # print("--\n\n")
            checklib.quit(checklib.Status.DOWN, "Cannot set flag",
                          "Service doesn't ask for signature")
        b = pwn.unhex(io.recvline().decode().replace(
            "\n", "").replace(" ", ""))
        assert len(b) == 16
        io.sendline(pwn.enhex(SK_CHECKER.sign(b)).encode())
        output = io.recvuntil(b"The value stack is empty")
        if b'The value stack is empty' not in output:
            # print("\n\n---")
            # print(output.decode())
            # print("--\n\n")
            checklib.quit(checklib.Status.DOWN, "Cannot set flag",
                          "Service doesn't reply after signature")
        io.recvuntil(b"Ready")
        io.close()
    except SystemExit:
        raise
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot set flag", str(e))
    checklib.quit(checklib.Status.OK, "OK")


def build_flag_name(flag):
    hash = hashlib.sha256(flag.encode())
    hx = hash.hexdigest()
    return "f" + hx[:30] + str(FLAG_STORE)


cmd_shortcuts = {
    'add': '+',
    'sub': '-',
    'mul': '*',
    'div': '/',
    'and': '&',
    'xor': '^',
    'or': '|',
    'help': '?'
}


def rand_bool():
    return random.randint(0, 1) == 0


def s():
    return ' ; ' if rand_bool() else '\n'


def encode_path(path: str):
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


def rand_encode(cmd, dont_recurse=False):
    r = random.randint(0, 1 if dont_recurse else 2)  # [a, b]
    if cmd in cmd_shortcuts and random.randint(0, 5) == 0:
        return cmd_shortcuts[cmd]
    if r == 0:
        return cmd.title()
    elif r == 1:
        return cmd.upper()
    elif r == 2:
        int_literal = encode_path(cmd_paths[cmd])
        if rand_bool():
            return f"{int_literal}!"
        else:
            if rand_bool():
                return f"{int_literal}{s()}{rand_encode('eval', True)}"
            else:
                return f"{int_literal}{s()}{encode_path(cmd_paths['eval'])}!"


def _push_int(i, level, ps):
    result = ""  # to make static-analysis happy
    i = ctypes.c_longlong(i).value
    r = random.randint(0, 5)  # [a, b]
    if level == 2 or r == 0:
        r = random.randint(0, 2)
        if r == 0:
            if i >= 0 and rand_bool():
                return f"+{i}{s()}"
            return f"{i}{s()}"
        elif r == 1:
            if i >= 0:
                return f"0x{hex(i)[2:].rjust(random.randint(0, 61), '0')}{s()}"
            else:
                return f"-0x{hex(i)[3:].rjust(random.randint(0, 60), '0')}{s()}"
        elif r == 2:
            if i >= 0:
                return f"0{oct(i)[2:].rjust(random.randint(0, 62), '0')}{s()}"
            else:
                return f"-0{oct(i)[3:].rjust(random.randint(0, 61), '0')}{s()}"
    level += 1
    # n = random.randint(-abs(i), abs(i))
    n = random.randint(MIN_LONG, MAX_LONG)
    if r == 1:  # Add and Sub
        if rand_bool():
            result = f"{_push_int(i-n, level, ps)}{_push_int(n, level, ps)}{rand_encode('add')}{s()}"
        else:
            if rand_bool():
                result = f"{_push_int(i+n, level, ps)}{_push_int(n, level, ps)}{rand_encode('swap')} ; {rand_encode('sub')}{s()}"
            else:
                result = f"{_push_int(n, level, ps)}{_push_int(i+n, level, ps)}{rand_encode('sub')}{s()}"
    elif r == 2:  # Or
        n &= i
        result = f"{_push_int(n, level, ps)}{_push_int(i, level, ps)}{rand_encode('or')}{s()}"
    elif r == 3:  # And
        n |= i
        result = f"{_push_int(n, level, ps)}{_push_int(i, level, ps)}{rand_encode('and')}{s()}"
    elif r == 4:  # Xor
        i ^= n
        result = f"{_push_int(n, level, ps)}{_push_int(i, level, ps)}{rand_encode('xor')}{s()}"
    elif r == 5:  # Useless drop
        if rand_bool():
            if rand_bool():  # plain
                result = f"{_push_int(n, level, ps)}{rand_encode('drop')}{s()}{_push_int(i, level, ps)}"
            else:  # with pick/swap
                result = f"{_push_int(i, level, ps)}{_push_int(n, level, ps)}"
                n_dup = random.randint(1, 3)  # esempio con 2
                for _ in range(n_dup):
                    result += f"{rand_encode('dup')}{s()}"
                    if rand_bool():
                        result += f"{rand_encode('swap')}{s()}"
                result += f"{rand_encode('drop')}{s()}"
                pick = "Pick" if rand_bool() else "PICK"
                result += f"{pick} {n_dup+1}{s()}"
                for _ in range(n_dup+1):
                    result += f"{rand_encode('swap')}{s()}{rand_encode('drop')}{s()}"
        else:  # with time/functions
            if rand_bool():
                result = f"{rand_encode('time')}{s()}"
                if rand_bool():
                    result += f"{rand_encode('time_to_str')}{s()}"
            else:
                result = f"{rand_encode('random')}{s()}"
            result += f"{_push_int(i, level, ps)}{rand_encode('swap')}{s()}{rand_encode('drop')}{s()}"
    if ps is not None:
        assert ps == 0 or ps == 1
        if random.randint(0, 3) == 0:
            result += f"{rand_encode('ps_status')}{s()}"
            if ps == 0:
                op = random.choice(['or', 'xor', 'add', 'sub'])
                result += f"{rand_encode('swap')}{s()}{rand_encode(op)}{s()}"
            else:
                result += f"{rand_encode('mul')}{s()}"
    elif random.randint(0, 3) == 0:
        result += f"{rand_encode('ps_status')}{s()}"
        n_dups = random.randint(0, 2)
        result += f"{rand_encode('swap')}{s()}"
        for _ in range(n_dups):
            result += f"{rand_encode('dup')}{s()}"
        result += f"SWAP {n_dups+1}{s()}"
        for _ in range(n_dups+1):
            result += f"{rand_encode('drop')}{s()}"
    return result


def push_int(i, ps):
    s = _push_int(i, 0, ps)
    if s.endswith(" ; "):
        s = s[:-3]
    if not s.endswith("\n"):
        s += "\n"
    return s


def _push_str_or_id(s_or_id):
    assert len(s_or_id) <= 32
    s_or_id = s_or_id.ljust(32, '\x00')
    result = ""
    ps = None
    for i in range(24, -8, -8):
        if random.randint(0, 2) == 0:
            r = random.randint(MIN_LONG, MAX_LONG)
            result += f"{push_int(r, ps)}{s()}{rand_encode('drop')}{s()}"
        r = random.randint(0, 2)
        if r == 0:
            pass  # do nothing
        elif r == 1:
            result += f"{rand_encode('ps_off')}{s()}"
            ps = 0
        else:
            result += f"{rand_encode('ps_on')}{s()}"
            ps = 1
        result += push_int(pwn.u64(s_or_id[i:i+8].encode('latin1')), ps)
    result += f"{rand_encode('ps_on')}{s()}"
    return result


def push_str(st):  # FIXME
    r = random.randint(0, 1)
    if r == 0:
        return f'{repr(st)}\n'
    return _push_str_or_id(st) + f"{rand_encode('ints_to_str')}\n"


def push_id(id):
    r = random.randint(0, 2)
    if r == 0:
        return _push_str_or_id(id) + f"{rand_encode('ints_to_id')}\n"
    elif r == 1:
        return f"{id}\n"
    elif r == 2:
        if rand_bool():
            return f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}{id}\n"
        else:
            return f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{id}{s()}{rand_encode('swap')}{s()}{rand_encode('drop')}\n"
    else:
        assert False


def wait_for_result(io):
    if rand_bool():
        io.sendline(rand_encode('help').encode())
        expected = 'Add the top two elements'
        recv = io.recvuntil(expected.encode()).decode('latin1')
        if expected not in recv:
            return False, recv
    else:
        io.sendline(rand_encode('ver').encode())
        expected = '982059cf01a70efb'
        recv = io.recvuntil(expected.encode()).decode('latin1')
        if expected not in recv:
            return False, recv
    recv += io.recvuntil(b'Ready').decode('latin1')
    return True, recv


def test_push_id(io):
    rand_str = random.choice(string.ascii_lowercase + "_")
    rand_str += "".join(random.sample(string.ascii_letters +
                        string.digits + "_", random.randint(1, 31)))
    # log.info(f'Testing push_id({rand_str})')
    encoding = push_id(rand_str).encode()
    io.send(encoding)
    wait_ok, s = wait_for_result(io)
    if not wait_ok:
        # print(s)
        # print("###")
        # print(encoding)
        # print("###")
        # print(encoding.decode())
        return False
    end = '[ 0] \x1b[0;32m'
    i = s.rfind(end)
    if i < 0:
        return False
    i += len(end)
    i2 = s.find('\x1b', i)
    if i2 < i:
        return False
    result = s[i:i2]
    if result != rand_str:
        # print(rand_str)
        # print(encoding.decode())
        # print(s)
        return False
    io.sendline(f"{rand_encode('drop')}\n".encode())
    return True


def test_push_str(io):
    escaped = "\n\r\t\"\'\\"
    safe_alphabet = string.ascii_letters + string.digits + "_={}[]"
    alphabet = safe_alphabet + escaped
    if random.randint(0, 30) == 0:
        rand_str = (
            "".join(random.sample(safe_alphabet, random.randint(8, 10)))
            + ("\\" * random.randint(1, 8))
            + "".join(random.sample(safe_alphabet, 7))
            + "".join(random.sample(alphabet, random.randint(0, 7)))
        )
        i = 42
    else:
        while True:
            rand_str = "".join(random.sample(alphabet, random.randint(0, 32)))
            i = rand_str.find("\\")
            c = rand_str.count("\\")
            if i == -1 or i > c:
                break
    # log.info(f'Testing push_str({repr(rand_str)})')
    encoding = push_str(rand_str).encode()
    io.send(encoding)
    if any(c in rand_str for c in escaped):
        rand_str = rand_str.encode()
        if i >= 0:
            rand_str = rand_str[rand_str.rindex(b"\\") + 1:]
            # log.info(f"Reducing rand_str to {repr(rand_str)}")
        if rand_str not in io.recvuntil(rand_str):
            # print(encoding)
            # print(encoding.decode())
            return False
        io.sendline(f"{rand_encode('drop')}\n".encode())
        return True
    wait_ok, s = wait_for_result(io)
    if not wait_ok:
        # print(encoding)
        # print(encoding.decode())
        return False
    end = '[ 0] \x1b[0;33m"'
    i = s.rfind(end)
    if i < 0:
        return False
    i += len(end)
    i2 = s.find('"\x1b', i)
    if i2 < i:
        return False
    result = s[i:i2]
    if result != rand_str:
        # print(rand_str)
        # print(encoding.decode())
        # print(s)
        return False
    io.sendline(f"{rand_encode('drop')}\n".encode())
    return True


def switch_to_base(base):
    result = ""
    if base == 8:
        if rand_bool():
            result += f"{rand_encode('dec')}{s()}"
            result += f"{rand_encode('next_base')}{s()}"
            result += f"{rand_encode('next_base')}{s()}"
        else:
            result += f"{rand_encode('oct')}{s()}"
    elif base == 10:
        result += f"{rand_encode('dec')}{s()}"
    elif base == 16:
        if rand_bool():
            result += f"{rand_encode('dec')}{s()}"
            result += f"{rand_encode('next_base')}{s()}"
        else:
            result += f"{rand_encode('hex')}{s()}"
    else:
        # log.error(f'switch_to_base: {base=}')
        pass
    if random.randint(0, 10) == 0:
        for _ in range(3 * random.randint(1, 5)):
            garbage = rand_bool()
            if garbage:
                result += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}"
            result += f"{rand_encode('next_base')}{s()}"
            if garbage:
                result += f"{rand_encode('drop')}{s()}"
    return result.encode()


def test_push_int(io):
    r = random.randint(MIN_LONG, MAX_LONG)
    # log.info(f'Testing push_int({r})')
    base = random.choice([8, 10, 16])
    encoding = switch_to_base(base) + push_int(r, None).encode()
    io.send(encoding)
    wait_ok, s = wait_for_result(io)
    if not wait_ok:
        # print(encoding.decode())
        return False
    end = '[ 0] \x1b[0;35m'
    i = s.rfind(end)
    if i < 0:
        return False
    i += len(end)
    i2 = s.find('\x1b', i)
    if i2 <= i:
        return False
    try:
        result = int(s[i:i2], base)
    except ValueError:
        return False
    if (result % 2**64) != (r % 2**64):
        # print("------ WHAT????? -----")
        # print('my random:', r, repr(r))
        # print('result   :', result, repr(result))
        # print(encoding)
        # print("###")
        # print(encoding.decode())
        # print("###")
        # print(s)
        # print(repr(s))
        return False
    io.sendline(f"{rand_encode('drop')}\n".encode())
    return True


def test_pushes():
    io = None
    for i in range(50000):
        if (i % 1000) == 0:
            if io:
                io.close()
            # io = pwn.process('../services/service3/src/rpn_with_asan')
            io = pwn.remote('127.0.0.1', 1337)
            if b'Ready' not in io.recvuntil(b'Ready'):
                # pwn.log.error("RPN is not ready")
                return False
        # log.info(f"test_pushes: {i=}")
        if not test_push_int(io):
            io.close()
            return False
        if not test_push_str(io):
            io.close()
            return False
        if not test_push_id(io):
            io.close()
            return False
        if not test_set_var(io):
            io.close()
            return False
    io.close()
    return True


def get_flag():
    io = connect_to_service()
    grab_banner(io)
    flag_value = data["flag"]
    flag_name = build_flag_name(flag_value)
    # log.info(f'get_flag({flag_value})')
    flag_value = flag_value.encode()
    try:
        commands = ""
        if rand_bool():
            commands += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}"
        commands += f"{push_id(flag_name)}"
        if rand_bool():
            commands += f"{push_int(random.randint(MIN_LONG, MAX_LONG), None)}{rand_encode('drop')}{s()}"
        commands += f"{rand_encode('get_var')}\n"
        io.send(commands.encode())
        if flag_value not in io.recvuntil(flag_value):
            checklib.quit(checklib.Status.DOWN, "Flag not found")
        io.close()
        checklib.quit(checklib.Status.OK, "OK")
    except SystemExit:
        raise
    except Exception as e:
        checklib.quit(checklib.Status.DOWN, "Cannot get flag", str(e))


def test_checker():
    def my_quit(exit_code, comment='', debug=''):
        if isinstance(exit_code, checklib.Status):
            exit_code = exit_code.value

        if exit_code != checklib.Status.OK.value:
            print(comment, file=sys.stderr)
            print(debug, file=sys.stderr)
            sys.exit(exit_code)

    if pwn.args.ERROR:
        pwn.context.log_level = logging.ERROR
    checklib.quit = my_quit
    global data, FLAG_STORE
    data = {}
    for round in range(10000):
        global ROUND
        ROUND = data['round'] = str(round)
        flags = ["".join(random.sample(string.ascii_uppercase +
                         string.digits, 31))+"=" for __ in range(16)]
        print(f'{round=}')  # {flags=}')
        for i in range(8):
            check_sla()
            FLAG_STORE = 1
            data['flag'] = flags[i]
            put_flag()
            FLAG_STORE = 2
            data['flag'] = flags[8 + i]
            put_flag()
        for i in range(8):
            check_sla()
            data['flag'] = flags[i]
            FLAG_STORE = 1
            get_flag()
            FLAG_STORE = 2
            data['flag'] = flags[8 + i]
            get_flag()
    return True


if __name__ != '__main__':
    if ACTION == checklib.Action.CHECK_SLA.name:
        check_sla()
    elif ACTION == checklib.Action.PUT_FLAG.name:
        put_flag()
    elif ACTION == checklib.Action.GET_FLAG.name:
        get_flag()
    else:
        assert False
else:
    # log.info("Testing pushes")
    # assert test_pushes()
    # log.info("Testing the checker")
    assert test_checker()
