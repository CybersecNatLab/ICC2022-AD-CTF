using System;
using System.ComponentModel.DataAnnotations.Schema;
using System.Numerics;

namespace service.Models;

public class Product
{
    public int Id { get; set; }

    [Column(TypeName = "VARCHAR(255)")] public string Name { get; set; } = null!;
    public string Description { get; set; } = null!;
    public string Content { get; set; } = null!;

    [Column(TypeName = "TEXT")] public BigInteger LicenseMod { get; set; } = BigInteger.Zero;
    [Column(TypeName = "TEXT")] public Polynomial LicensePoly { get; set; } = new();

    public DateTime CreatedAt { get; set; } = DateTime.Now;


    public int UserId { get; set; }
    public virtual User User { get; set; } = null!;
}
