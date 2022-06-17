using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using service.Models;
using service.Services;

namespace service.Controllers;

[ApiController]
[Route("api")]
public class AuthController : BaseController
{
    private readonly HMacSigner _signer;

    public AuthController(ApplicationDbContext db, HMacSigner signer) : base(db)
    {
        _signer = signer;
    }

    [HttpPost]
    [Route("login")]
    public async Task<ActionResult> Login()
    {
        var username = Request.Form["username"].ToString();
        var password = Request.Form["password"].ToString();

        if (username == "" || password == "" || username.Length > 255 || password.Length > 255)
        {
            return UnprocessableEntity("Invalid Input");
        }

        var user = await Database.Users.SingleOrDefaultAsync(u => u.Username == username && u.Password == password);
        if (user == null)
        {
            return NotFound();
        }

        return Ok(new
        {
            user_id = user.Id,
            session = _signer.Sign(user.Id + user.Username),
        });
    }

    [HttpPost]
    [Route("register")]
    public async Task<ActionResult> Register()
    {
        var username = Request.Form["username"].ToString();
        var password = Request.Form["password"].ToString();

        if (username == "" || password == "" || username.Length > 255 || password.Length > 255)
        {
            return UnprocessableEntity();
        }

        var existingUser = await Database.Users.SingleOrDefaultAsync(u => u.Username == username);
        if (existingUser != null)
        {
            return Conflict();
        }

        var user = new User
        {
            Username = username,
            Password = password,
            CreatedAt = DateTime.Now,
        };
        Database.Users.Add(user);
        await Database.SaveChangesAsync();

        return StatusCode(StatusCodes.Status201Created, new
        {
            user_id = user.Id,
            session = _signer.Sign(user.Id + user.Username),
        });
    }
}
