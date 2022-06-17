using System;

namespace service.Extensions;

public static class ObjectExt
{
    public static TResult Let<TSource, TResult>(this TSource obj, Func<TSource, TResult> selector)
    {
        return selector(obj);
    }
}
