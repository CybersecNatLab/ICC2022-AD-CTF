using System.Numerics;
using Microsoft.EntityFrameworkCore;
using service.Models;

namespace service;

public class ApplicationDbContext : DbContext
{
    public DbSet<User> Users { get; set; } = null!;
    public DbSet<Product> Products { get; set; } = null!;

    protected override void OnConfiguring(DbContextOptionsBuilder options) =>
        options.UseLazyLoadingProxies()
            .UseSqlite($"Data Source=data/data.db");

    protected override void ConfigureConventions(ModelConfigurationBuilder builder)
    {
        builder
            .Properties<BigInteger>()
            .HaveConversion<BigIntegerConverter>();

        builder
            .Properties<Polynomial>()
            .HaveConversion<PolynomialConverter>();
    }
}
