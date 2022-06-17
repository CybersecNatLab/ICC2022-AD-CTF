using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using service.Extensions;
using service.Models;
using service.Services;

namespace service.Middlewares;

public class AuthMiddleware
{
    private readonly RequestDelegate _next;
    private readonly HMacSigner _signer;

    private readonly List<string> _blacklist = new()
    {
        "/api/login",
        "/api/register",
    };

    public AuthMiddleware(RequestDelegate next, HMacSigner signer)
    {
        _next = next;
        _signer = signer;
    }

    private static string? GetToken(HttpRequest request)
    {
        var auth = request.Headers.Authorization.FirstOrDefault();
        if (auth == null || !auth.StartsWith("Bearer "))
        {
            return null;
        }

        var token = auth[7..];
        return token == "" ? null : token;
    }

    private async Task<User?> FetchUser(HttpRequest request, ApplicationDbContext db)
    {
        var token = GetToken(request);
        if (token == null)
        {
            return null;
        }

        var decoded = Encoding.ASCII.GetString(Convert.FromBase64String(token));
        var parts = decoded.Split(":");
        if (parts.Length != 2)
        {
            return null;
        }

        try
        {
            var userId = int.Parse(parts[0]);
            var user = await db.Users.SingleAsync(u => u.Id == userId);

            return _signer.Validate(user.Id + user.Username, parts[1]) ? user : null;
        }
        catch (FormatException)
        {
            return null;
        }
        catch (InvalidOperationException)
        {
            return null;
        }
    }

    public async Task InvokeAsync(HttpContext context, ApplicationDbContext db)
    {
        if (_blacklist.Any(context.Request.FullPath().Contains))
        {
            await _next(context);
            return;
        }

        var user = await FetchUser(context.Request, db);
        if (user == null)
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            return;
        }

        context.Items["user"] = user;

        await _next(context);
    }
}
