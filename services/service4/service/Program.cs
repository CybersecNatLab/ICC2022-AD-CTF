using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;

namespace service;

public class Program
{
    public static void Main(string[] args)
    {
        Host.CreateDefaultBuilder(args)
            .ConfigureWebHostDefaults(builder =>
            {
                builder
                    .UseStartup<Startup>()
                    .UseUrls("http://0.0.0.0:5000/");
            })
            .UseConsoleLifetime()
            .Build()
            .Run();
    }
}
