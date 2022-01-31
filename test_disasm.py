#!/usr/bin/env python

from lr35902dis.lr35902 import *
from struct import pack
from binascii import hexlify

ADDR = 0xDEAD

import binaryninja

arch = None
def disasm_binja(data, addr):
    global arch
    if not arch:
        arch = binaryninja.Architecture['LR35902']
    toksAndLen = arch.get_instruction_text(data, addr)
    if not toksAndLen or toksAndLen[1]==0:
        return ''
    toks = toksAndLen[0]
    strs = map(lambda x: x.text, toks)
    return ''.join(strs)

def disasm_lr35902dis(data, addr):
    return disasm(data, addr)

for i in range(65536):
    data = pack('>H', i) + b'\xAB\xCD\xEF\x00'

    a = disasm_binja(data, ADDR)
    b = disasm_lr35902dis(data, ADDR)

    hexstr = hexlify(data[0:6]).decode('utf-8')
    print('%04X: %s -%s- -%s-' % (ADDR, hexstr.ljust(16), a, b))

    assert a == b

