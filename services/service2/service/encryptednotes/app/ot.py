from Crypto.Util.number import getPrime, inverse
from Crypto.Random import random
import gmpy2


class Sender:
    def __init__(self, m):
        self.m = m
        p, q = getPrime(512), getPrime(512)
        e, N = 65537, p*q
        phi = (p-1)*(q-1)
        d = inverse(e, phi)

        self.N = N
        self.e = e
        self.d = d

    def round1(self):
        x = [(random.randrange(1 << 128), random.randrange(1 << 128))]*len(self.m)
        self.x = x
        return (self.N, self.e), x

    def round3(self, v):
        n = len(v)
        assert n == len(self.m)
        c = []
        for i in range(n):
            k = [int(gmpy2.powmod(v[i]-t, self.d, self.N)) for t in self.x[i]]
            cc = [(kk+mm) % self.N for kk, mm in zip(k, self.m[i])]
            c.append(cc)
        return c


class Receiver:
    def __init__(self, b):
        self.b = b

    def round2(self, pk, x):
        N, e = pk
        n = len(x)
        assert n == len(self.b)

        v = []
        k = []
        for i in range(n):
            kk = random.randrange(1 << 2048)
            k.append(kk)
            cur = x[i][self.b[i]] + pow(kk, e, N)
            v.append(cur % N)
        self.k = k
        self.N = N
        return v

    def decode(self, c):
        n = len(c)
        assert n == len(self.b)

        m = []
        for i in range(n):
            mm = (c[i][self.b[i]]-self.k[i]) % self.N
            m.append(mm)
        return m
