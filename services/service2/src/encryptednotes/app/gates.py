from hashlib import sha256
import os
from itertools import product

VAL_LENGTH = 5
PAD_LENGTH = 3


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def rnd():
    return os.urandom(VAL_LENGTH)


def H(k):
    return sha256(k).digest()


def enc(k, out):
    k = H(k)
    val = b"\0"*PAD_LENGTH + out
    return xor(k, val)


def dec(k, x):
    k = H(k)
    val = xor(k, x)
    if val[:PAD_LENGTH] == b"\0"*PAD_LENGTH:
        return val[PAD_LENGTH:]


OPS = {
    "AND": lambda x, y: x & y,
    "XOR": lambda x, y: x ^ y,
    "INV": lambda x: 1-x
}


class Gate:
    def __init__(self, idx, inputs, op, opv):
        self.idx = idx
        self.inputs = inputs
        self.op = op
        self.opv = opv

    def garble(self, R):
        if hasattr(self, "_cache"):
            return self._cache
        self._cache = self._garble(R)
        return self._cache

    def _garble(self, R):
        n = len(self.inputs)
        for g in self.inputs:
            g.garble(R)

        if self.opv == "XOR":
            val = xor(self.inputs[0].wires[0], self.inputs[1].wires[0])
            self.wires = [val, xor(val, R)]
            self.gate = []
            return

        if self.opv == "INV":
            w = self.inputs[0].wires
            self.wires = [w[1], w[0]]
            self.gate = []
            return

        r = rnd()
        wires = [r, xor(r, R)]
        g = []
        for e in product(range(2), repeat=n):
            k = b"".join(self.inputs[i].wires[e[i]] for i in range(n))
            res = self.op(*e)
            val = enc(k, wires[res])
            g.append(val)

        self.wires = wires
        self.gate = g

    def encode(self, to_hex):
        gate = self.gate
        if to_hex:
            gate = [r.hex() for r in gate]
        return (self.idx, self.opv, [x.idx for x in self.inputs], gate)

    def encode_wires(self, to_hex):
        wires = self.wires
        if to_hex:
            wires = [wires[0].hex(), wires[1].hex()]
        return wires

    def visit(self):
        if hasattr(self, "_vcache"):
            return self._vcache
        self._vcache = self._visit()
        return self._vcache

    def _visit(self):
        if self.opv == "INV":
            return f"NOT ({self.inputs[0].visit()})"
        a = self.inputs[0].visit()
        if len(a) >= 10000:
            return "TRUNC"
            return f"{self.idx}"
        b = self.inputs[1].visit()
        if len(b) >= 10000:
            return "TRUNC"
            return f"{self.idx}"
        return f"({a}) {self.opv} ({b})"


class Input(Gate):
    def __init__(self, idx):
        self.idx = idx

    def _garble(self, R):
        r = rnd()
        self.wires = [r, xor(r, R)]

    def visit(self):
        return str(self.idx)


def decode_gate(opv, g, ins, to_hex):
    if to_hex:
        ins = [bytes.fromhex(x) for x in ins]
        g = [bytes.fromhex(r) for r in g]
    if opv == "INV":
        res = ins[0]
    elif opv == "XOR":
        res = xor(ins[0], ins[1])
    else:
        for x in g:
            k = b"".join(ins)
            val = dec(k, x)
            if val is not None:
                res = val
                break
    if to_hex:
        return res.hex()
    return res


INDEX = 0
def get_idx():
    global INDEX
    val = INDEX
    INDEX += 1
    return val


def build_circuit_custom():
    global INDEX
    INDEX = 0

    inputA = [Input(get_idx()) for i in range(4)]
    inputB = [Input(get_idx()) for i in range(4)]

    gates1 = [Gate(get_idx(), [inputA[i], inputB[i]], OPS["AND"], "AND") for i in range(4)]
    gates2 = [Gate(get_idx(), [gates1[0], gates1[1]], OPS["XOR"], "XOR"), Gate(get_idx(), [gates1[2], gates1[3]], OPS["XOR"], "XOR")]
    out = Gate(get_idx(), [gates2[0], gates2[1]], OPS["XOR"], "XOR")

    gates = gates1+gates2
    return (inputA, inputB), gates, [out]


def build_circuit_echo(n=128):
    global INDEX
    INDEX = 0
    inputA = [Input(get_idx()) for i in range(n)]
    inputB = [Input(get_idx()) for i in range(n)]

    f = lambda x, y: y

    out = [Gate(get_idx(), [inputA[i], inputB[i]], f, "OP1") for i in range(n)]
    return (inputA, inputB), [], out


def build_circuit_AES(filename):
    with open(filename) as f:
        the_order = []
        ngates, nwires = map(int, f.readline().strip().split())
        niv, *nis = map(int, f.readline().strip().split())
        nov, *nos = map(int, f.readline().strip().split())
        f.readline()
        inputA = [Input(i) for i in range(nis[0])]
        inputB = [Input(i) for i in range(nis[0], nis[0]+nis[1])]
        inputs = inputA+inputB

        gates = inputs + [None for _ in range(nwires - sum(nis))]
        for j in range(ngates):
            i, o, *op, out, g = f.readline().strip().split()
            op = list(map(int, op))
            out = int(out)
            the_order.append(out)
            i = int(i)
            o = int(o)
            assert o == 1
            assert gates[out] is None
            assert all(gates[x] is not None for x in op)
            gate = Gate(out, [gates[x] for x in op], OPS[g], g)
            gates[out] = gate
        assert not any(x is None for x in gates)
    n_outs = sum(nos)
    n_ins = sum(nis)
    last = nwires-n_outs
    inner_gates = []
    output_gates = []
    for x in the_order:
        if x >= last:
            output_gates.append(gates[x])
        else:
            inner_gates.append(gates[x])
    return (inputA, inputB), inner_gates, output_gates


def build_circuit_AES128():
    return build_circuit_AES("aes_128.txt")


def garble(circuit, true_input, to_hex=True):
    (inputA, inputB), gates, outputs = circuit
    R = rnd()
    for out in outputs:
        out.garble(R)

    encoded_inputA = [Ain.encode_wires(to_hex)[x] for Ain, x in zip(inputA, true_input)]
    encoded_inputB = [Bin.encode_wires(to_hex) for Bin in inputB]

    encoded_gates = [x.encode(to_hex) for x in gates+outputs]
    wires_out = [x.encode_wires(to_hex) for x in sorted(outputs, key=lambda el: el.idx)]

    return (encoded_inputA, encoded_inputB), encoded_gates, wires_out


def evaluate(garbled_circuit, inputs, wires_out, to_hex=True):
    enc_A, enc_B = inputs
    vals = enc_A+enc_B+[None]*len(garbled_circuit)
    for g in garbled_circuit:
        idx, opv, ins, gate = g
        k = [vals[i] for i in ins]
        cur = decode_gate(opv, gate, k, to_hex)
        assert cur is not None
        vals[idx] = cur

    n_outs = len(wires_out)
    vals_out = vals[-n_outs:]
    out = [w.index(v) for v, w in zip(vals_out, wires_out)]
    return out
