using System;
using System.Globalization;

namespace service.Extensions;

public static class DateTimeExt
{
    public static string ToIsoZulu(this DateTime time)
    {
        return time.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffK", CultureInfo.InvariantCulture);
    }
}
