#!/usr/bin/env python3
import sys

with open('rpn', 'rb') as f:
    exe = bytearray(f.read())


def change(orig, patch):
    assert len(orig) != 0 and len(orig) == len(patch)
    offs = exe.find(orig)
    if offs < 0:
        print(
            f"Cannot find the original sequence {repr(orig)} (executable already patched?)")
        return False
    if exe.find(orig, offs+1) != -1:
        print("The byte sequence can be found in multiple places")
        return False
    for i, b in enumerate(patch):
        exe[offs + i] = b
    return True


'''
    Patch #1
'''
# 000046c1  89c2               mov     edx, eax
# 000046c3  83e21f             and     edx, 0x1f
# 000046c6  8915f4590100       mov     dword [rel data_1a0c0], edx
# 000046cc  a803               test    al, 0x3
# Change 0x1f to 0x03
if not change(b'\x83\xe2\x1f',
              b'\x83\xe2\x03'):
    sys.exit()


'''
    Patch #2
'''
# 00003d3d  3c5c               cmp     al, 0x5c
# 00003d3f  0f8495feffff       je      0x3bda
# NOP the je
if not change(b'\x0f\x84\x95\xfe\xff\xff',
              b'\x90\x90\x90\x90\x90\x90'):
    sys.exit()


'''
    Patch #3
'''
# 00003894  83c201             add     edx, 0x1
# 00003897  83fa3f             cmp     edx, 0x3f
# 0000389a  776b               ja      0x3907
# change 0x3f to 0x3e
if not change(b'\x83\xc2\x01\x83\xfa\x3f',
              b'\x83\xc2\x01\x83\xfa\x3e'):
    sys.exit()


'''
    Patch #4
'''
# 00003125  488b1d34860100     mov     rbx, qword [rel data_1b760]
# 0000312c  85db               test    ebx, ebx
# 0000312e  0f8496000000       je      0x31ca
# 00003134  8d43ff             lea     eax, [rbx-0x1]
# change je to jle
if not change(b'\x0f\x84\x96\x00\x00\x00',
              b'\x0f\x8e\x96\x00\x00\x00'):
    sys.exit()


'''
    Patch #5
'''
# 00003fe8  48bfc995c9012929…  mov     rdi, 0x1e5b292901c995c9
# 00003ff2  e8fbebffff         call    print_error
# 00003ff7  8305e6f6050001     add     dword [rel stack_len], 0x1
# 00003ffe  ebd1               jmp     0x3fd1
# remove the add
if not change(b'\x83\x05\xe6\xf6\x05\x00\x01',
              b'\x90\x90\x90\x90\x90\x90\x90'):
    sys.exit()


'''
    Patch #6
'''
# 00012258  char const data_12258[0x1c] = "Unix-time out of range: %sd", 0
# replace %sd with %jd
if not change(b"Unix-time out of range: %sd",
              b"Unix-time out of range: %jd"):
    sys.exit()


'''
    Patch #7
'''
# 0000336f  488b05ea830100     mov     rax, qword [rel data_1b760]
# 00003376  4885c0             test    rax, rax
# 00003379  0f85fdfeffff       jne     0x327c
# 0000337f  48bfe0fbbb0a50ab…  mov     rdi, 0x24cdab500abbfbe0
# replace jne with jns
if not change(b'\x0f\x85\xfd\xfe\xff\xff',
              b'\x0f\x89\xfd\xfe\xff\xff'):
    sys.exit()


'''
    Patch #8
'''
# 00003e28  488b5308           mov     rdx, qword [rbx+0x8]
# 00003e2c  4881fa11badd00     cmp     rdx, 0xddba11
# 00003e33  742a               je      0x3e5f
# NOP je
if not change(b'\xba\xdd\x00\x74\x2a',
              b'\xba\xdd\x00\x90\x90'):
    sys.exit()

'''
    Patch #9
'''
# 000190a0  uint32_t counter.1 = 0xffffffff
# counter should be initialized with 0
offset = 0x180a0
for i in range(4):
    assert exe[offset+i] == 255
    exe[offset+i] = 0

with open('rpn', 'wb') as f:
    f.write(exe)
