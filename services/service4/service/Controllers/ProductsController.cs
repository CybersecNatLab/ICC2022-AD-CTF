using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using service.Extensions;
using service.Models;
using service.Services;

namespace service.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : BaseController
{
    private const int LicensesToGenerate = 5;

    private readonly LicenseService _licenses;

    public ProductsController(ApplicationDbContext db, LicenseService licenses) : base(db)
    {
        _licenses = licenses;
    }

    [HttpGet]
    public ActionResult Index()
    {
        return Ok(
            Auth()?.Products
                .OrderByDescending(p => p.CreatedAt)
                .Select(p => new
                {
                    id = p.Id,
                    publisher_id = p.UserId,
                    name = p.Name,
                    description = p.Description,
                    license = new
                    {
                        mod = p.LicenseMod,
                        poly = p.LicensePoly,
                    },
                    created_at = p.CreatedAt.ToIsoZulu(),
                })
        );
    }

    [HttpGet]
    [Route("{id:int}")]
    public async Task<ActionResult> Show(int id)
    {
        var product = await Database.Products.SingleOrDefaultAsync(p => p.Id == id);
        if (product == null)
        {
            return NotFound();
        }

        return Ok(new
        {
            id = product.Id,
            publisher = new
            {
                id = product.User.Id,
                username = product.User.Username,
            },
            name = product.Name,
            description = product.Description,
            license = new
            {
                mod = product.LicenseMod,
                poly = product.LicensePoly,
            },
            created_at = product.CreatedAt.ToIsoZulu(),
        });
    }

    [HttpPost]
    public async Task<ActionResult> Store()
    {
        var name = Request.Form["name"].ToString();
        var description = Request.Form["description"].ToString();
        var content = Request.Form["content"].ToString();

        if (name == "" || content == "" || name.Length > 255 || description.Length > 32768 || content.Length > 32768)
        {
            return UnprocessableEntity("Invalid Input");
        }

        var product = new Product
        {
            Name = name,
            Description = description,
            Content = content,
            CreatedAt = DateTime.Now,
            UserId = Auth()!.Id,
        };
        Database.Products.Add(product);
        await Database.SaveChangesAsync();

        var (poly, mod, licenses) = await _licenses.GenerateLicenses(product.Id.ToString(), LicensesToGenerate);

        product.LicenseMod = mod;
        product.LicensePoly = poly;
        Database.Products.Update(product);
        await Database.SaveChangesAsync();

        return StatusCode(StatusCodes.Status201Created, new
        {
            id = product.Id,
            publisher_id = product.UserId,
            name = product.Name,
            description = product.Description,
            license = new
            {
                mod = product.LicenseMod,
                poly = product.LicensePoly,
            },
            keys = licenses,
            created_at = product.CreatedAt.ToIsoZulu(),
        });
    }
}
