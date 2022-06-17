using System;
using System.Security.Cryptography;
using System.Text;

namespace service.Services;

public class HMacSigner
{
    private readonly byte[] _key;

    public HMacSigner(string key)
    {
        _key = Encoding.ASCII.GetBytes(key);
    }

    public string Sign(string data)
    {
        return BitConverter
            .ToString(new HMACSHA256(_key).ComputeHash(Encoding.ASCII.GetBytes(data)))
            .Replace("-", "")
            .ToLower();
    }

    public bool Validate(string data, string signature)
    {
        return CryptographicOperations.FixedTimeEquals(
            Encoding.ASCII.GetBytes(signature),
            Encoding.ASCII.GetBytes(Sign(data))
        );
    }
}
