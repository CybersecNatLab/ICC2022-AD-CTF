using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;
using Microsoft.EntityFrameworkCore;

namespace service.Models;

[Index(nameof(Username), IsUnique = true)]
public class User
{
    public int Id { get; set; }

    [Column(TypeName = "VARCHAR(255)")] public string Username { get; set; } = null!;
    [Column(TypeName = "VARCHAR(255)")] public string Password { get; set; } = null!;

    public DateTime CreatedAt { get; set; } = DateTime.Now;


    public virtual ICollection<Product> Products { get; set; } = null!;
}
