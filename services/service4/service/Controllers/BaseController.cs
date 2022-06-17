using Microsoft.AspNetCore.Mvc;
using service.Models;

namespace service.Controllers;

public class BaseController : ControllerBase
{
    protected readonly ApplicationDbContext Database;

    public BaseController(ApplicationDbContext db)
    {
        Database = db;
    }

    protected User? Auth()
    {
        return (User?)HttpContext.Items["user"];
    }
}
