using Microsoft.AspNetCore.Http;

namespace service.Extensions;

public static class HttpRequestExt
{
    public static string FullPath(this HttpRequest request)
    {
        return (request.Path.HasValue ? request.Path.ToString() : "/") + request.QueryString;
    }
}
