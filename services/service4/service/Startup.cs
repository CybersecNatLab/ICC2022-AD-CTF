using System;
using System.Security.Cryptography;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.ResponseCompression;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using service.Middlewares;
using service.Models;
using service.Services;

namespace service;

public class Startup
{
    public Startup(IConfiguration configuration)
    {
        Configuration = configuration;
    }

    private IConfiguration Configuration { get; }

    public void ConfigureServices(IServiceCollection services)
    {
        services.AddDbContext<ApplicationDbContext>();

        // TODO(to players): Add a 32 bytes random key to appsettings.json System.SignatureKey field to persist data across restarts.
        if (Configuration["System:SignatureKey"] == "")
        {
            Configuration["System:SignatureKey"] = Convert.ToBase64String(RandomNumberGenerator.GetBytes(24));
        }

        services.AddSingleton(_ => new HMacSigner(Configuration["System:SignatureKey"]));
        services.AddSingleton(_ => new OpenSsl(Configuration["System:OpensslPath"]));
        services.AddSingleton(provider => new LicenseService(provider.GetService<OpenSsl>()!, Configuration["System:SignatureKey"]));

        services.AddControllers().AddJsonOptions(options =>
        {
            options.JsonSerializerOptions.Converters.Add(new BigIntegerSerializer());
            options.JsonSerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
        });

        services.AddResponseCompression(options =>
        {
            options.EnableForHttps = true;
            options.Providers.Add<BrotliCompressionProvider>();
            options.Providers.Add<GzipCompressionProvider>();
        });
    }

    public void Configure(IApplicationBuilder app, IWebHostEnvironment env, ApplicationDbContext dataContext)
    {
        dataContext.Database.Migrate();

        app.UseResponseCompression();
        app.UseRouting();
        app.UseDefaultFiles();
        app.UseStaticFiles();

        app.UseMiddleware<AuthMiddleware>();

        app.UseEndpoints(endpoints => { endpoints.MapControllers(); });
    }
}
