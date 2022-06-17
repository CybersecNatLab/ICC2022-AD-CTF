using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Numerics;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace service.Models;

public class Polynomial : Collection<BigInteger>
{
    public Polynomial()
    {
    }

    public Polynomial(IList<BigInteger> list) : base(list)
    {
    }

    public Polynomial(int capacity) : base(new List<BigInteger>(capacity))
    {
    }

    public void AddRange(IEnumerable<BigInteger> list)
    {
        foreach (var i in list)
        {
            Add(i);
        }
    }
}

public class PolynomialConverter : ValueConverter<Polynomial, string>
{
    private static JsonSerializerOptions JsonOptions => new()
    {
        Converters = { new BigIntegerSerializer() },
    };

    public PolynomialConverter()
        : base(
            v => JsonSerializer.Serialize(v, JsonOptions),
            s => JsonSerializer.Deserialize<Polynomial>(s, JsonOptions)!
        )
    {
    }
}

public class BigIntegerConverter : ValueConverter<BigInteger, string>
{
    public BigIntegerConverter()
        : base(
            v => v.ToString(NumberFormatInfo.InvariantInfo),
            s => BigInteger.Parse(s, NumberFormatInfo.InvariantInfo)
        )
    {
    }
}

public class BigIntegerSerializer : JsonConverter<BigInteger>
{
    public override BigInteger Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.String)
            throw new JsonException($"Found token {reader.TokenType} but expected token {JsonTokenType.Number}");
        return BigInteger.Parse(reader.GetString()!, NumberFormatInfo.InvariantInfo);
    }

    public override void Write(Utf8JsonWriter writer, BigInteger value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value.ToString(NumberFormatInfo.InvariantInfo));
    }
}
