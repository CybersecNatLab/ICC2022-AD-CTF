using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using service.Models;

namespace service.Services;

public class LicenseService
{
    private readonly OpenSsl _openssl;
    private readonly SHA512 _sha512;
    private readonly string _secret;

    public LicenseService(OpenSsl openssl, string secret)
    {
        _openssl = openssl;
        _sha512 = SHA512.Create();
        _secret = secret;
    }

    private static Polynomial MultiplyPoly(Polynomial a, Polynomial b, BigInteger mod)
    {
        var n = a.Count + b.Count - 1;
        var res = new Polynomial(n);
        res.AddRange(Enumerable.Repeat(BigInteger.Zero, n));

        for (var i = 0; i < a.Count; i++)
        {
            for (var j = 0; j < b.Count; j++)
            {
                res[i + j] += a[i] * b[j];
                res[i + j] %= mod;
            }
        }

        return res;
    }

    private static BigInteger EvaluatePoly(Polynomial poly, BigInteger value, BigInteger mod)
    {
        var res = BigInteger.Zero;

        for (var i = 0; i < poly.Count; i++)
        {
            res += poly[i] * BigInteger.ModPow(value, i, mod);
            res %= mod;
        }

        return res;
    }

    private static IEnumerable<int> NumberToList(BigInteger x)
    {
        return x < 26
            ? new List<int> { (int)x }
            : new List<int> { (int)(x % 26) }.Concat(NumberToList(x / 26)).ToList();
    }

    private static string LicenseToString(BigInteger value)
    {
        var l = string.Join("", NumberToList(value).Select(x => (char)(x + 0x41)));
        while (l.Length % 7 != 0)
        {
            l += "A";
        }

        return string.Join("-", Enumerable.Range(0, l.Length / 7)
            .Select(i => l.Substring(i * 7, 7)));
    }

    private static BigInteger RandomBigInteger(int bits)
    {
        var rng = RandomNumberGenerator.Create();
        var bytes = new byte[bits / 8];
        rng.GetBytes(bytes);
        return BigInteger.Abs(new BigInteger(bytes));
    }

    public async Task<Tuple<Polynomial, BigInteger, List<string>>> GenerateLicenses(string seeder, int n)
    {
        var module = await _openssl.Prime(1024);
        var poly = MultiplyPoly(
            new Polynomial { BigInteger.Zero, BigInteger.One },
            new Polynomial { BigInteger.Abs(new BigInteger(_sha512.ComputeHash(Encoding.ASCII.GetBytes(_secret + seeder)))), BigInteger.One },
            module
        );

        var licences = Enumerable.Repeat(0, n).Select(_ => RandomBigInteger(128)).ToList();
        poly = licences.Aggregate(poly, (current, licence) => MultiplyPoly(current, new Polynomial { -licence, BigInteger.One }, module));

        return new Tuple<Polynomial, BigInteger, List<string>>(
            poly,
            module,
            licences.Select(LicenseToString).ToList()
        );
    }

    public bool VerifyLicense(Polynomial poly, BigInteger mod, string key)
    {
        if (!Regex.Match(key, "^([A-Z]{7})-([A-Z]{7})-([A-Z]{7})-([A-Z]{7})$").Success)
        {
            return false;
        }

        var n = key.Replace("-", "")
            .ToCharArray()
            .Select((ch, i) => BigInteger.Pow(26, i) * (ch - 0x41))
            .Aggregate(BigInteger.Zero, (current, n) => current + n);

        return EvaluatePoly(poly, n, mod) == BigInteger.Zero;
    }
}
