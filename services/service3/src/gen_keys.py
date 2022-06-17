#!/usr/bin/env python3
# Generate *s*igning and *v*erifying keys
import ed25519_blake2b

N = 8
with open("v_keys.c", "w") as out_c, open("s_keys.py", "w") as out_py:
    skeys = []
    for i in range(N):
        sk, vk = ed25519_blake2b.create_keypair()
        skeys.append(sk.to_bytes())
        with open(f"sk{i}","wb") as f:
            f.write(sk.to_bytes())
        with open(f"vk{i}","wb") as f:
            b = vk.to_bytes()
            print(f'const uint8_t vk_{i}[32] = ', str(list(b)).replace("[","{").replace("]","}"), ';', sep='', file=out_c)
            f.write(b)
    print('const uint8_t * const v_keys[]={', file=out_c)
    for i in range(N):
        print(f'\tvk_{i},', file=out_c)
    print(f'\t0,', file=out_c)
    print('};', file=out_c)
    for i, keydata in enumerate(skeys):
        print((f"SK_CHECKER" if i==0 else f"_team{i}_skey") +
               f" = ed25519_blake2b.SigningKey({repr(keydata)})", file=out_py)
    print("_teams_signing_keys = [", end="", file=out_py);
    for i in range(1, N):
        print(f"_team{i}_skey, ", end="", file=out_py)
    print("]", file=out_py)

