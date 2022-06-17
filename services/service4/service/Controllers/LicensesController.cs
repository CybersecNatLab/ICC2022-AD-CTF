using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using service.Extensions;
using service.Services;

namespace service.Controllers;

[ApiController]
[Route("api/products")]
public class LicensesController : BaseController
{
    private readonly LicenseService _licenses;

    public LicensesController(ApplicationDbContext db, LicenseService licenses) : base(db)
    {
        _licenses = licenses;
    }

    [HttpPost]
    [Route("{id:int}/download")]
    public async Task<ActionResult> Download(int id)
    {
        var product = await Database.Products.SingleOrDefaultAsync(p => p.Id == id);
        if (product == null)
        {
            return NotFound();
        }

        if (Auth()?.Let(user => user.Id != product.UserId) == true)
        {
            var license = Request.Form["license"].ToString();
            if (license == "")
            {
                return UnprocessableEntity("Invalid Input");
            }

            if (!_licenses.VerifyLicense(product.LicensePoly, product.LicenseMod, license))
            {
                return StatusCode(StatusCodes.Status403Forbidden);
            }
        }

        Response.Headers.Add("Content-Disposition", $"attachment; filename=\"{product.Id}.txt\"");
        return Ok(product.Content);
    }
}
